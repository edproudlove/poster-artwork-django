from django.shortcuts import render
from django.views import generic, View
from . import models
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import HttpResponse, HttpResponseRedirect
import re
from django.urls import reverse_lazy, reverse
import stripe
from django.core.mail import send_mail
from django.conf import settings
from django.views import View, generic
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json


from django.shortcuts import render
from .forms import ArtistUserForm, ArtistUserProfileInfoForm

# Extra Imports for the Login and Logout Capabilities
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required


# Create your views here.
import string
import random

stripe.api_key = settings.STRIPE_SECRET_KEY


shipping_price_dict = {
    '£4: Standard Delivery, 4-6 Working days': 4,
    '£7.50: Express Delivery, 2-4 Working days': 7,
    '£10: Next Day Delivery, 1 Working day': 10,
}


def id_generator(size=15, chars=string.ascii_uppercase): #+ string.digits):
   return ''.join(random.choice(chars) for _ in range(size))

def refactor_price_string(price_string, *args):
    size, price = price_string.split('-')
    numbers = re.findall(r'\d+', price)
    string_version = ''
    for integer in numbers:
        string_version += integer
    float_version = float(string_version) / 100
    return size, float_version

class IndexView(generic.ListView):
    template_name = 'poster_app/index.html'
    model = models.PosterModel
    context_object_name = 'posters'


class DetailPosterView(generic.DetailView):
    template_name = 'poster_app/detail_poster.html'
    model = models.PosterModel
    context_object_name = 'poster'

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            device = request.COOKIES['device']
            customer, created = models.Customer.objects.get_or_create(device=device)
            #order_ref = id_generator(12)
            #it needs to get a ref_code when created that is unique 
            live_order, created = models.LiveOrder.objects.get_or_create(customer=customer)
            if created:
                live_order.save()
            
            #if created:
            #    order.ref_code = order_ref
            #    print('created')
            #    order.save()
            #else:
            #    print(order.ref_code)
                

            if 'price' in request.POST:
                if 'quantity' in request.POST:
                    current_item_pk = kwargs['pk']
                    current_item = models.PosterModel.objects.get(pk=current_item_pk)
                    price_string = request.POST['price']

                    size, price = refactor_price_string(price_string)
                    quantity = request.POST['quantity']

                    order_item = models.OrderItem(product = current_item, price=price, quantity=quantity, size=size)
                    order_item.save()
                    live_order.items.add(order_item)
                    return HttpResponseRedirect(self.request.path_info)

                else:
                    print('Error Reciving the Qantity')
                    return redirect('/') 

            else:
                print('Error Reciving the Price')
                return redirect('/')
    





class CartView(generic.TemplateView):
    template_name = 'poster_app/cartview.html'
    
    


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        device = self.request.COOKIES['device']
        customer, created = models.Customer.objects.get_or_create(device=device)
        context['order'] = models.LiveOrder.objects.get_or_create(customer=customer)[0]
        return context










class DeleteFromBasketView(generic.DeleteView):
    model = models.OrderItem
    template_name = 'poster_app/delete_from_basket.html'
    success_url = reverse_lazy('poster_app:cart')
    context_object_name = 'orderitem'


#######################################################    


class CheckOutView(generic.TemplateView): 
    template_name = 'poster_app/check_out_view.html'

    def get_context_data(self, **kwargs):
        device = self.request.COOKIES['device']
        customer, created = models.Customer.objects.get_or_create(device=device)
        live_order, created = models.LiveOrder.objects.get_or_create(customer = customer)
        if created:
            live_order.save()
            print("CREATED LIVE ORDER")
        context = super(CheckOutView, self).get_context_data(**kwargs)
        context.update({
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
            'order': live_order

        })
        return context





class StripeIntentView(View):
    #possible error in that the amount should be in pence
    def post(self, request, *args, **kwargs):
        print('CREATING-PAYMENT-INTENT')
        try:
            req_json = json.loads(request.body)
            customer = stripe.Customer.create(email=req_json['email'], name=req_json['name'])
            shipping_info = [req_json['street_address'], req_json['city'], req_json['postcode'],]
            delivery_option = req_json['delivery_option']

            shipping_price = int(100 * shipping_price_dict[delivery_option])

            live_order_id = self.kwargs['pk']
            live_order = models.LiveOrder.objects.get(id=live_order_id)
            intent = stripe.PaymentIntent.create(
                amount=int(live_order.get_cart_total()*100 + shipping_price),
                currency='usd',
                customer=customer['id'],
                metadata={
                    'customer_email':req_json['email'],
                    'customer_name':req_json['name'],
                    'live_order_id':live_order.id,
                    'street_address': shipping_info[0],
                    'city': shipping_info[1],
                    'postcode': shipping_info[2],
                    'delivery_option': delivery_option,
                }
            )
            print(intent['client_secret'])
            return JsonResponse({
                'clientSecret': intent['client_secret']
            })
        except Exception as e:
            return JsonResponse({'error':str(e), })






@csrf_exempt
def stripe_webhook_view(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Passed signature verification
    if event['type'] == 'payment_intent.succeeded':
        # Here i will input a fucntion that is called to reorganise the databases and move the order into an orderd row


        intent = event['data']['object']

        stripe_customer_id = intent['customer']
        stripe_customer = stripe.Customer.retrieve(stripe_customer_id)

        live_order_id = intent['metadata']['live_order_id']
        shipping_info = intent['metadata']['street_address']
        delivery_option = intent['metadata']['delivery_option']
        customer_email = intent['metadata']['customer_email']
        customer_name = intent['metadata']['customer_name']




        live_order = models.LiveOrder.objects.get(id=live_order_id)
        paid_price = live_order.get_cart_total() + shipping_price_dict[delivery_option]
        

        #Convert From live to paid order and delete the live order object:

        current_products = ''
        for product in live_order.items.all():
            current_products += f'[{product.product.title},{product.size},{product.quantity}],'


        paid_order, created = models.PaidOrder.objects.get_or_create(order_ref=live_order.ref_code)
        paid_order.shipping_details = shipping_info
        paid_order.shipping_option = delivery_option
        paid_order.price_paid = str(paid_price)
        paid_order.customer_email = customer_email
        paid_order.customer_name = customer_name
        paid_order.products = current_products
        paid_order.save()
        print('CONVERTING PRODUCT')

        ###################################################################


        

        send_mail(
            subject='Here Is Your Order',
            message=f'Thankyou For Your Purchanse Of {live_order.ref_code}!, You paid £{paid_price:.2f}, shipping info: {shipping_info},delivery option: {delivery_option}',
            
            recipient_list=[stripe_customer['email']],
            from_email='posters@gmail.com'
        )
    return HttpResponse(status=200)



class CancelView(generic.TemplateView):
    template_name = 'poster_app/cancelled.html'

class SuccessView(generic.TemplateView):
    template_name = 'poster_app/success.html'

#things to change in order to get this to wokr how i want is:
# - shipping adress






####################LOGING IN###############################

@login_required
def user_logout(request):
    # Log out the user.
    logout(request)
    # Return to homepage.
    return HttpResponseRedirect(reverse('poster_app:index'))

def register(request):

    registered = False

    if request.method == 'POST':

        # Get info from "both" forms
        # It appears as one form to the user on the .html page
        user_form = ArtistUserForm(data=request.POST)
        profile_form = ArtistUserProfileInfoForm(data=request.POST)

        # Check to see both forms are valid
        if user_form.is_valid() and profile_form.is_valid():

            # Save User Form to Database
            user = user_form.save()

            # Hash the password
            user.set_password(user.password)

            # Update with Hashed password
            user.save()

            # Now we deal with the extra info!

            # Can't commit yet because we still need to manipulate
            profile = profile_form.save(commit=False)

            # Set One to One relationship between
            # UserForm and UserProfileInfoForm
            profile.user = user

            # Check if they provided a profile picture
            if 'profile_pic' in request.FILES:
                print('found it')
                # If yes, then grab it from the POST form reply
                profile.profile_pic = request.FILES['profile_pic']

            # Now save model
            profile.save()

            # Registration Successful!
            registered = True

        else:
            # One of the forms was invalid if this else gets called.
            print(user_form.errors,profile_form.errors)

    else:
        # Was not an HTTP post so we just render the forms as blank.
        user_form = ArtistUserForm()
        profile_form = ArtistUserProfileInfoForm()

    # This is the render and context dictionary to feed
    # back to the registration.html file page.
    return render(request,'poster_app/registration.html',
                          {'user_form':user_form,
                           'profile_form':profile_form,
                           'registered':registered})

def user_login(request):

    if request.method == 'POST':
        # First get the username and password supplied
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Django's built-in authentication function:
        user = authenticate(username=username, password=password)

        # If we have a user
        if user:
            #Check it the account is active
            if user.is_active:
                # Log the user in.
                login(request,user)
                # Send the user back to some page.
                # In this case their homepage.
                return HttpResponseRedirect(reverse('poster_app:index'))
            else:
                # If account is not active:
                return HttpResponse("Your account is not active.")
        else:
            print("Someone tried to login and failed.")
            print("They used username: {} and password: {}".format(username,password))
            return HttpResponse("Invalid login details supplied.")

    else:
        #Nothing has been provided for username or password.
        return render(request, 'poster_app/login.html', {})