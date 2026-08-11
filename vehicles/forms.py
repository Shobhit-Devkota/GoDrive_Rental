from datetime import date
from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    with_driver = forms.ChoiceField(
        choices=[('0', 'Self Drive'), ('1', 'Book with a Driver')],
        widget=forms.RadioSelect,
        initial='0',
    )

    class Meta:
        model = Booking
        fields = ['full_name', 'phone', 'email', 'with_driver', 'start_date', 'end_date']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[var(--deep-blue)] focus:border-transparent',
                'placeholder': 'Your full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[var(--deep-blue)] focus:border-transparent',
                'placeholder': '98XXXXXXXX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[var(--deep-blue)] focus:border-transparent',
                'placeholder': 'you@example.com'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'id': 'id_start_date',
                'class': 'w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[var(--deep-blue)] focus:border-transparent'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'id': 'id_end_date',
                'class': 'w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[var(--deep-blue)] focus:border-transparent'
            }),
        }

    def __init__(self, *args, vehicle=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Needed to check date conflicts against THIS vehicle's other bookings
        self.vehicle = vehicle or (self.instance.vehicle if self.instance and self.instance.pk else None)
        if self.instance and self.instance.pk:
            self.fields['with_driver'].initial = '1' if self.instance.with_driver else '0'

    def clean_with_driver(self):
        return self.cleaned_data['with_driver'] == '1'

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')

        if start and start < date.today():
            raise forms.ValidationError("Pickup date cannot be in the past.")

        if start and end and end <= start:
            raise forms.ValidationError("Return date must be after the pickup date.")

        if start and end and self.vehicle:
            overlapping = Booking.objects.filter(
                vehicle=self.vehicle,
                status__in=['pending', 'confirmed'],
                start_date__lt=end,
                end_date__gt=start,
            )
            if self.instance and self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise forms.ValidationError(
                    "This vehicle is already booked for part of these dates. Please choose different dates."
                )
# we need to return clean data
        return cleaned_data