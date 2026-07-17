from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal


class Brand(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    TRANSMISSION_CHOICES = [
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
    ]
    FUEL_CHOICES = [
        ('electric', 'Electric'),
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('hybrid', 'Hybrid'),
    ]

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='vehicles')
    model_name = models.CharField(max_length=100)
    description = models.TextField()
    seats = models.PositiveSmallIntegerField(default=4)
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='automatic')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='petrol')
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(
        default=True,
        help_text="Untick to hide this vehicle from the site entirely (e.g. sold, retired, under repair). "
                   "This is independent of bookings — do NOT use this to mark a vehicle as booked; "
                   "that happens automatically once a customer's booking is confirmed."
    )
    is_featured = models.BooleanField(default=False, help_text="Show this vehicle on the homepage")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand.name} {self.model_name}"

    def get_absolute_url(self):
        return reverse('vehicles:detail', args=[self.pk])

    @property
    def is_available(self):
        """
        Computed live from actual bookings — never stored, so it can never go stale or
        get overwritten. A vehicle is available only if it's active AND has no
        pending/confirmed booking currently against it.
        """
        if not self.is_active:
            return False
        return not self.bookings.filter(status__in=['pending', 'confirmed']).exists()

    @property
    def main_image(self):
        img = self.images.order_by('order').first()
        return img.url() if img else ''


class VehicleImage(models.Model):
    ANGLE_CHOICES = [
        ('front', 'Front'),
        ('side', 'Side'),
        ('rear', 'Rear'),
        ('interior', 'Interior'),
    ]
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    image_url = models.URLField(blank=True, help_text="Used if no image file is uploaded (placeholder/demo images)")
    angle = models.CharField(max_length=20, choices=ANGLE_CHOICES, default='front')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.vehicle} - {self.angle}"

    def url(self):
        if self.image:
            return self.image.url
        return self.image_url


class Destination(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    extra_charge_per_day = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Add to daily rate for this destination. Use a negative number to give a discount instead."
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Booking(models.Model):
    STATUS_CHOICES = [
        ('awaiting_payment', 'Awaiting Advance Payment'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    ADVANCE_PERCENTAGE = Decimal('0.05')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bookings')
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True)

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    start_date = models.DateField()
    end_date = models.DateField()

    total_days = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='awaiting_payment')

    is_verified = models.BooleanField(default=False, help_text="Ticked once an admin has manually verified this booking")
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_bookings')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.pk} - {self.vehicle} by {self.full_name}"

    @property
    def advance_amount(self):
        """5% of the total price, required upfront via eSewa to secure the booking."""
        return (self.total_price * self.ADVANCE_PERCENTAGE).quantize(Decimal('0.01'))

    @property
    def remaining_amount(self):
        return self.total_price - self.advance_amount


class Payment(models.Model):
    """Tracks the 5% advance payment made via eSewa to secure a booking."""
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    METHOD_CHOICES = [
        ('auto', 'Automatic (eSewa redirect)'),
        ('manual', 'Manual (customer-reported reference)'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    transaction_uuid = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='auto')
    esewa_ref_id = models.CharField(max_length=100, blank=True, help_text="Transaction code returned by eSewa on success")
    manual_reference = models.CharField(
        max_length=100, blank=True,
        help_text="Customer-entered eSewa reference, used when the automatic eSewa redirect isn't reachable. "
                   "Check this against your own eSewa transaction history before verifying the booking."
    )
    raw_response = models.TextField(blank=True, help_text="Decoded eSewa callback response, kept for troubleshooting")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Booking #{self.booking_id} - {self.status}"
