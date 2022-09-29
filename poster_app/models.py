from django.db import models
import string
import random
from django.contrib.auth.models import User
# Create your models here.

class PosterModel(models.Model):
    title = models.CharField(max_length=124)
    author = models.CharField(max_length=124)
    image = models.ImageField(upload_to='images/')
    #size = models.CharField(max_length=20, choices=[('A4', 'MEDIUM'),('A5', 'LARGE'),('A3', 'SMALL')])
    date_added = models.DateTimeField(auto_now=True)
    price_of_medium = models.IntegerField()

    def __str__(self):
        return self.title


class Customer(models.Model):
    device = models.CharField(max_length=200)

    def __str__(self):
        return self.device
    


class Artist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    posters = models.ManyToManyField(PosterModel)
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    profile_pic = models.ImageField(upload_to='images/profile_pics',blank=True)

    def __str__(self):
        return self.user.username
    



####### THIS IS FOR THE CART AND CART ITEMS #########

class OrderItem(models.Model):
    #this is just an item that is in the cart ready to be orderd

    product = models.ForeignKey(PosterModel, on_delete=models.SET_NULL, null=True)
    is_ordered = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now=True)
    date_ordered = models.DateTimeField(null=True)
    price = models.FloatField()
    quantity = models.PositiveIntegerField()
    size = models.CharField(max_length=200)

    #could try passing the size and threfore price into this model when it is added to the cart
    #then in the order model we could do for price in item.price

    def __str__(self):
        return self.product.title





def id_generator(size=15, chars=string.ascii_uppercase): #+ string.digits):
   return ''.join(random.choice(chars) for _ in range(size))



class LiveOrder(models.Model):
    #this is like hte cart model its self
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, null=True)
    ref_code = models.CharField(max_length=15, unique=True, blank=False, null=False)
    is_ordered = models.BooleanField(default=False)
    items = models.ManyToManyField(OrderItem)
    date_ordered = models.DateTimeField(auto_now=True)
    
    def get_cart_items(self):
        return self.items.all()

    #this may need revising to add in the diffrent sizes
    def get_cart_total(self):
        return sum([(item.price * item.quantity) for item in self.items.all() ])

    def __str__(self):
        return self.ref_code

    def save(self, *args, **kwargs):
        self.ref_code = id_generator(15)
        super(LiveOrder, self).save(*args, **kwargs)




class PaidOrder(models.Model):
    order_ref = models.CharField(max_length=20)
    date_orderd = models.DateField(auto_now_add=True)
    shipping_details = models.CharField(max_length=1000)
    shipping_option = models.CharField(max_length=100)
    products = models.TextField(max_length=1000)
    price_paid = models.CharField(max_length=10)
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=100)

    def __str__(self):
        return self.order_ref

    def save(self, *args, **kwargs):
        LiveOrder.objects.filter(ref_code=self.order_ref).delete()
        super(PaidOrder, self).save(*args, **kwargs)


