from django import forms
from .models import ContactMessage

INPUT_CLASSES = (
    'w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none '
    'focus:ring-2 focus:ring-[var(--deep-blue)] focus:border-transparent'
)


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Your name'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'you@example.com'}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': '98XXXXXXXX (optional)'}),
            'subject': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': INPUT_CLASSES, 'placeholder': 'Your message', 'rows': 5}),
        }
