from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['full_name', 'phone', 'email', 'destination', 'start_date', 'end_date']
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
            'destination': forms.Select(attrs={
                'id': 'id_destination',
                'class': 'w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[var(--deep-blue)] focus:border-transparent'
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

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end <= start:
            raise forms.ValidationError("Return date must be after the pickup date.")
        return cleaned_data
