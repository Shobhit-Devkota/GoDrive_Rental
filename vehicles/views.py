import uuid
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Min, Max, Q
from django.urls import reverse
from .models import Brand, Vehicle, Destination, Booking, Payment
from .forms import BookingForm
from . import esewa

REGULAR_CUSTOMER_THRESHOLD = 2  # 2 or more bookings = regular customer


def category_list(request, brand_slug=None):
    vehicles = Vehicle.objects.select_related('brand').prefetch_related('images')
    active_brand = None
    query = request.GET.get('q', '').strip()

    if brand_slug:
        active_brand = get_object_or_404(Brand, slug=brand_slug)
        vehicles = vehicles.filter(brand=active_brand)
    elif query:
        vehicles = vehicles.filter(
            Q(brand__name__icontains=query) | Q(model_name__icontains=query)
        )

    # Top 5 brands (by how many vehicles they have) shown as quick search suggestions
    top_brands = Brand.objects.annotate(
        vehicle_count=Count('vehicles')
    ).order_by('-vehicle_count', 'name')[:5]

    context = {
        'vehicles': vehicles,
        'active_brand': active_brand,
        'query': query,
        'top_brands': top_brands,
    }
    return render(request, 'vehicles/category.html', context)


def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle.objects.prefetch_related('images'), pk=pk)
    related = Vehicle.objects.filter(brand=vehicle.brand).exclude(pk=pk)[:3]
    return render(request, 'vehicles/detail.html', {'vehicle': vehicle, 'related': related})


@login_required
def book_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    destinations = Destination.objects.all()

    if not vehicle.is_available:
        messages.error(request, "Sorry, this vehicle is currently booked and not available.")
        return redirect('vehicles:detail', pk=pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.vehicle = vehicle

            days = (booking.end_date - booking.start_date).days
            daily_rate = vehicle.price_per_day
            extra = booking.destination.extra_charge_per_day if booking.destination else 0
            total = (daily_rate + extra) * days
            if total < 0:
                total = 0

            booking.total_days = days
            booking.total_price = total
            booking.status = 'awaiting_payment'
            booking.save()

            # Create the 5% advance payment record and send the customer to eSewa
            Payment.objects.create(
                booking=booking,
                transaction_uuid=f"gorental-{booking.pk}-{uuid.uuid4().hex[:10]}",
                amount=booking.advance_amount,
                status='initiated',
            )

            return redirect('vehicles:initiate_payment', pk=booking.pk)
    else:
        form = BookingForm()

    context = {
        'vehicle': vehicle,
        'form': form,
        'destinations': destinations,
    }
    return render(request, 'vehicles/booking.html', context)


@login_required
def initiate_payment(request, pk):
    """Shows a short summary and auto-submits the hidden eSewa payment form."""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if booking.status != 'awaiting_payment':
        return redirect('vehicles:booking_success', pk=booking.pk)

    success_url = request.build_absolute_uri(reverse('vehicles:payment_success'))
    failure_url = request.build_absolute_uri(reverse('vehicles:payment_failure', args=[booking.pk]))

    payload = esewa.build_payment_payload(booking, success_url, failure_url)

    context = {
        'booking': booking,
        'payload': payload,
        'esewa_payment_url': settings.ESEWA_PAYMENT_URL,
    }
    return render(request, 'vehicles/initiate_payment.html', context)


@login_required
def submit_manual_payment(request, pk):
    """
    Fallback for when eSewa's automated redirect is unreachable (their shared sandbox is
    known to be flaky). The customer pays manually via the eSewa app and reports the
    reference number here; the booking then waits for an admin to verify it by hand.
    """
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if booking.status != 'awaiting_payment':
        return redirect('vehicles:booking_success', pk=booking.pk)

    if request.method == 'POST':
        reference = request.POST.get('manual_reference', '').strip()
        if not reference:
            messages.error(request, "Please enter the eSewa transaction reference you received.")
            return redirect('vehicles:initiate_payment', pk=booking.pk)

        payment = getattr(booking, 'payment', None)
        if payment:
            payment.method = 'manual'
            payment.manual_reference = reference
            payment.save()

        booking.status = 'pending'
        booking.save()

        messages.success(
            request,
            "Thanks — we've recorded your payment reference. Your booking is now pending "
            "manual verification by our team."
        )
        return redirect('vehicles:booking_success', pk=booking.pk)

    return redirect('vehicles:initiate_payment', pk=booking.pk)


@login_required
def payment_success(request):
    """eSewa redirects here with ?data=<base64 json> after a successful payment."""
    encoded_data = request.GET.get('data')
    response_data = esewa.decode_esewa_response(encoded_data) if encoded_data else None

    if not response_data:
        messages.error(request, "We couldn't read the payment response from eSewa. Please contact support.")
        return redirect('vehicles:my_bookings')

    signature_valid = esewa.verify_response_signature(response_data, settings.ESEWA_SECRET_KEY)
    transaction_uuid = response_data.get('transaction_uuid', '')
    payment = Payment.objects.filter(transaction_uuid=transaction_uuid).select_related('booking').first()

    if not payment:
        messages.error(request, "We couldn't find a matching payment record. Please contact support.")
        return redirect('vehicles:my_bookings')

    status_check = esewa.check_transaction_status(
        settings.ESEWA_STATUS_CHECK_URL,
        settings.ESEWA_MERCHANT_CODE,
        str(payment.amount),
        transaction_uuid,
    )
    status_confirmed = bool(status_check) and status_check.get('status') == 'COMPLETE'

    if signature_valid and response_data.get('status') == 'COMPLETE' and status_confirmed:
        payment.status = 'success'
        payment.esewa_ref_id = response_data.get('transaction_code', '')
        payment.raw_response = str(response_data)
        payment.save()

        booking = payment.booking
        booking.status = 'pending'  # awaiting admin verification, advance is paid
        booking.save()

        messages.success(request, "Advance payment received. Your booking is now pending verification by our team.")
    else:
        payment.status = 'failed'
        payment.raw_response = str(response_data)
        payment.save()
        messages.error(request, "Payment could not be verified. Please try again or contact support.")

    return redirect('vehicles:booking_success', pk=payment.booking.pk)


@login_required
def payment_failure(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    payment = getattr(booking, 'payment', None)
    if payment:
        payment.status = 'failed'
        payment.save()
    messages.error(request, "Your eSewa payment was not completed. You can try again from your bookings page.")
    return redirect('vehicles:my_bookings')


@login_required
def booking_success(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    return render(request, 'vehicles/booking_success.html', {'booking': booking})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('vehicle', 'destination')
    return render(request, 'vehicles/my_bookings.html', {'bookings': bookings})


@login_required
def edit_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if booking.is_verified or booking.status in ('cancelled', 'completed'):
        messages.error(request, "This booking can no longer be edited — it has already been verified/finalized.")
        return redirect('vehicles:my_bookings')

    destinations = Destination.objects.all()

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            updated_booking = form.save(commit=False)

            days = (updated_booking.end_date - updated_booking.start_date).days
            daily_rate = booking.vehicle.price_per_day
            extra = updated_booking.destination.extra_charge_per_day if updated_booking.destination else 0
            total = (daily_rate + extra) * days
            if total < 0:
                total = 0

            updated_booking.total_days = days
            updated_booking.total_price = total
            updated_booking.save()

            # Keep the linked payment amount consistent with the new total (5% advance)
            payment = getattr(updated_booking, 'payment', None)
            if payment and payment.status != 'success':
                payment.amount = updated_booking.advance_amount
                payment.save()

            messages.success(request, "Your booking has been updated.")
            return redirect('vehicles:my_bookings')
    else:
        form = BookingForm(instance=booking)

    context = {
        'booking': booking,
        'vehicle': booking.vehicle,
        'form': form,
        'destinations': destinations,
        'is_edit': True,
    }
    return render(request, 'vehicles/booking.html', context)


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if booking.is_verified or booking.status in ('cancelled', 'completed'):
        messages.error(request, "This booking can no longer be cancelled — it has already been verified/finalized.")
        return redirect('vehicles:my_bookings')

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, "Your booking has been cancelled.")
        return redirect('vehicles:my_bookings')

    return render(request, 'vehicles/cancel_booking_confirm.html', {'booking': booking})


@user_passes_test(lambda u: u.is_staff, login_url='accounts:login')
def admin_dashboard(request):
    """Staff-only report: every customer, whether they're regular or new,
    when they first/last booked, and their full booking history."""

    search = request.GET.get('q', '').strip()

    customers = (
        User.objects.filter(bookings__isnull=False)
        .select_related('profile')
        .annotate(
            booking_count=Count('bookings'),
            first_booking_at=Min('bookings__created_at'),
            last_booking_at=Max('bookings__created_at'),
        )
        .prefetch_related('bookings__vehicle', 'bookings__destination')
        .distinct()
        .order_by('-booking_count', '-last_booking_at')
    )

    if search:
        customers = customers.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(bookings__phone__icontains=search) |
            Q(bookings__full_name__icontains=search)
        ).distinct()

    total_bookings = Booking.objects.count()
    total_customers = customers.count()
    regular_customers = sum(1 for c in customers if c.booking_count >= REGULAR_CUSTOMER_THRESHOLD)

    all_bookings = Booking.objects.select_related('vehicle', 'vehicle__brand', 'destination', 'user').order_by('-created_at')

    context = {
        'customers': customers,
        'all_bookings': all_bookings,
        'regular_threshold': REGULAR_CUSTOMER_THRESHOLD,
        'total_bookings': total_bookings,
        'total_customers': total_customers,
        'regular_customers': regular_customers,
        'search': search,
    }
    return render(request, 'vehicles/admin_dashboard.html', context)
