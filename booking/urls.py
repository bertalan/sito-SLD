from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.BookingView.as_view(), name='booking'),
    path('slots/<str:date>/', views.get_available_slots, name='api_slots'),
    path('checkout/', views.CreateCheckoutSession.as_view(), name='checkout'),
    path('success/', views.BookingSuccessView.as_view(), name='success'),
    path('cancel/', views.BookingCancelView.as_view(), name='cancel'),
    path('webhook/', views.stripe_webhook, name='webhook'),
    path('paypal/execute/', views.paypal_execute, name='paypal_execute'),
]
