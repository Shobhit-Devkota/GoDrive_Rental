from django.contrib import admin
from django.db.models import Count
from django.utils import timezone
from django.utils.html import format_html
from .models import Brand, Vehicle, VehicleImage, Destination, Booking, Payment

REGULAR_CUSTOMER_THRESHOLD = 2


class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 1


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['brand', 'model_name', 'price_per_day', 'availability_display', 'is_active', 'is_featured']
    list_filter = ['brand', 'is_active', 'is_featured', 'transmission', 'fuel_type']
    search_fields = ['model_name', 'brand__name']
    readonly_fields = ['availability_display']
    inlines = [VehicleImageInline]

    def availability_display(self, obj):
        if obj.is_available:
            return format_html('<span style="color:#0D9488;font-weight:600;">{}</span>', 'Available')
        return format_html('<span style="color:#DC2626;font-weight:600;">{}</span>', 'Booked')
    availability_display.short_description = 'Live Availability (computed from bookings)'


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ['name', 'extra_charge_per_day']
    prepopulated_fields = {'slug': ('name',)}


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ['transaction_uuid', 'amount', 'status', 'method', 'esewa_ref_id', 'manual_reference', 'raw_response', 'created_at', 'updated_at']
    can_delete = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Superusers and staff with Booking permissions get full add/change/delete access by default.
    list_display = [
        'id', 'full_name', 'customer_username', 'phone', 'email',
        'vehicle', 'destination', 'start_date', 'end_date',
        'total_days', 'total_price', 'advance_amount_display', 'payment_status',
        'status', 'verified_flag', 'customer_type', 'created_at',
    ]
    list_display_links = ['id', 'full_name']
    list_editable = ['status']
    list_filter = ['status', 'is_verified', 'destination', 'vehicle__brand', 'created_at']
    search_fields = ['full_name', 'email', 'phone', 'user__username']
    readonly_fields = ['total_days', 'total_price', 'created_at', 'customer_type', 'verified_at', 'verified_by']
    date_hierarchy = 'created_at'
    inlines = [PaymentInline]
    actions = ['verify_bookings', 'unverify_bookings', 'mark_confirmed', 'mark_cancelled']

    def customer_username(self, obj):
        return obj.user.username
    customer_username.short_description = 'Username'

    def customer_type(self, obj):
        count = Booking.objects.filter(user=obj.user).count()
        return f"Regular ({count} bookings)" if count >= REGULAR_CUSTOMER_THRESHOLD else f"New ({count} booking)"
    customer_type.short_description = 'Customer Type'

    def advance_amount_display(self, obj):
        return f"NPR {obj.advance_amount}"
    advance_amount_display.short_description = 'Advance (5%)'

    def payment_status(self, obj):
        payment = getattr(obj, 'payment', None)
        if not payment:
            return format_html('<span style="color:#9CA3AF;">{}</span>', 'No payment')
        colors = {'success': '#0D9488', 'failed': '#DC2626', 'initiated': '#9CA3AF'}
        color = colors.get(payment.status, '#9CA3AF')
        return format_html('<span style="color:{};font-weight:600;">{}</span>', color, payment.get_status_display())
    payment_status.short_description = 'eSewa Payment'

    def verified_flag(self, obj):
        if obj.is_verified:
            return format_html('<span style="color:#0D9488;font-weight:600;">{}</span>', '✓ Verified')
        return format_html('<span style="color:#DC2626;">{}</span>', 'Not Verified')
    verified_flag.short_description = 'Verification'

    @admin.action(description="Verify selected bookings (marks as confirmed)")
    def verify_bookings(self, request, queryset):
        updated = 0
        for booking in queryset:
            booking.is_verified = True
            booking.verified_at = timezone.now()
            booking.verified_by = request.user
            booking.status = 'confirmed'
            booking.save()
            updated += 1
        self.message_user(request, f"{updated} booking(s) verified and confirmed.")

    @admin.action(description="Remove verification from selected bookings")
    def unverify_bookings(self, request, queryset):
        updated = queryset.update(is_verified=False, verified_at=None, verified_by=None)
        self.message_user(request, f"{updated} booking(s) marked as not verified.")

    @admin.action(description="Mark selected bookings as Confirmed")
    def mark_confirmed(self, request, queryset):
        updated = 0
        for booking in queryset:
            booking.status = 'confirmed'
            booking.save()  # per-instance save so the vehicle-availability signal fires
            updated += 1
        self.message_user(request, f"{updated} booking(s) marked as confirmed.")

    @admin.action(description="Mark selected bookings as Cancelled")
    def mark_cancelled(self, request, queryset):
        updated = 0
        for booking in queryset:
            booking.status = 'cancelled'
            booking.save()  # per-instance save so the vehicle becomes available again
            updated += 1
        self.message_user(request, f"{updated} booking(s) marked as cancelled.")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'amount', 'method', 'status', 'esewa_ref_id', 'manual_reference', 'created_at']
    list_filter = ['status', 'method']
    search_fields = ['transaction_uuid', 'esewa_ref_id', 'manual_reference', 'booking__full_name']
    readonly_fields = ['transaction_uuid', 'amount', 'esewa_ref_id', 'raw_response', 'created_at', 'updated_at']
