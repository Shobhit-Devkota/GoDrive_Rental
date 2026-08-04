from django import forms
from .models import ContactMessage

INPUT_CLASSES = (
    'w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none '
    'focus:ring-2 focus:ring-[var(--deep-blue)] focus:border-transparent'
)

SUBJECT_CHOICES = [
    ('', 'Select a topic'),
    ('Booking Inquiry', 'Booking Inquiry'),
    ('Vehicle Availability', 'Vehicle Availability'),
    ('Payment / Refund', 'Payment / Refund'),
    ('Feedback', 'Feedback'),
    ('Other', 'Other'),
]


class ContactForm(forms.ModelForm):
    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        widget=forms.Select(attrs={'class': INPUT_CLASSES}),
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Your name'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'you@example.com'}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': '98XXXXXXXX (optional)'}),
            'message': forms.Textarea(attrs={'class': INPUT_CLASSES, 'placeholder': 'Your message', 'rows': 7}),
        }