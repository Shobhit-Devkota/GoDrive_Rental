from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.category_list, name='category_list'),
    path('brand/<slug:brand_slug>/', views.category_list, name='category_by_brand'),
    path('<int:pk>/', views.vehicle_detail, name='detail'),
    path('<int:pk>/book/', views.book_vehicle, name='book'),
    path('booking/<int:pk>/pay/', views.initiate_payment, name='initiate_payment'),
    path('booking/<int:pk>/pay/manual/', views.submit_manual_payment, name='submit_manual_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/<int:pk>/failure/', views.payment_failure, name='payment_failure'),
    path('booking/<int:pk>/success/', views.booking_success, name='booking_success'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<int:pk>/edit/', views.edit_booking, name='edit_booking'),
    path('booking/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-actions/<int:pk>/confirm/', views.admin_confirm_booking, name='admin_confirm_booking'),
    path('admin-actions/<int:pk>/cancel/', views.admin_cancel_booking, name='admin_cancel_booking'),
    path('admin-actions/<int:pk>/verify/', views.admin_verify_booking, name='admin_verify_booking'),
    path('admin-actions/<int:pk>/edit/', views.admin_edit_booking, name='admin_edit_booking'),
]
