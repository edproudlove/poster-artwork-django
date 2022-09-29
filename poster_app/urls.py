from . import views
from django.urls import path, include

app_name = 'poster_app'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('detail_poster/<int:pk>/', views.DetailPosterView.as_view(), name='detail_poster_view'),
    path('cart', views.CartView.as_view(), name='cart'),
    path('checkout', views.CheckOutView.as_view(), name='checkout'),
    path('remove/<int:pk>/', views.DeleteFromBasketView.as_view(), name='delete_from_basket'),
    path('webhooks/stripe', views.stripe_webhook_view, name='stripe-webhook'),
    path('create-payment-intent/<pk>/', views.StripeIntentView.as_view(), name='create-payment-intent'),
    path('success/', views.SuccessView.as_view(), name='success'),
    path('cancelled/', views.CancelView.as_view(), name='cancelled'),
    path('artist_register/',views.register,name='artist_register'),
    path('artist_login/',views.user_login,name='artist_login'),
    
]

   
   
   