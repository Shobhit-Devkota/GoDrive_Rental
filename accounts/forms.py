import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

INPUT_CLASSES = (
    'w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none '
    'focus:ring-2 focus:ring-[var(--deep-blue)] focus:border-transparent'
)

# Nepali mobile numbers: 10 digits, starting with 97 or 98 (NTC/Ncell ranges).
NEPALI_PHONE_REGEX = re.compile(r'^(97|98)\d{8}$')

# Shobhit
# class RegisterForm(UserCreationForm):
#     email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
#         'class': INPUT_CLASSES, 'placeholder': 'you@example.com'
#     }))
#     phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={
#         'class': INPUT_CLASSES, 'placeholder': '98XXXXXXXX'
#     }))

#     class Meta:
#         model = User
#         fields = ['username', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': INPUT_CLASSES, 'placeholder': 'Choose a username'})
        self.fields['password1'].widget.attrs.update({'class': INPUT_CLASSES, 'placeholder': 'Create a password'})
        self.fields['password2'].widget.attrs.update({'class': INPUT_CLASSES, 'placeholder': 'Confirm password'})

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip().replace(' ', '').replace('-', '')
        if not NEPALI_PHONE_REGEX.match(phone):
            raise forms.ValidationError(
                "Enter a valid 10-digit Nepali mobile number starting with 97 or 98 (e.g. 98XXXXXXXX)."
            )
        return phone

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.profile.phone = self.cleaned_data['phone']
            user.profile.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': INPUT_CLASSES, 'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': INPUT_CLASSES, 'placeholder': 'Password'
    }))


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': INPUT_CLASSES, 'placeholder': 'The email you registered with'
    }))

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("We couldn't find an account with that email.")
        return email


class ResetCodeForm(forms.Form):
    code = forms.CharField(max_length=6, widget=forms.TextInput(attrs={
        'class': INPUT_CLASSES + ' text-center tracking-[0.5em] font-bold text-lg',
        'placeholder': '000000', 'maxlength': '6'
    }))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': INPUT_CLASSES, 'placeholder': 'New password'
    }))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': INPUT_CLASSES, 'placeholder': 'Confirm new password'
    }))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("The two password fields didn't match.")
        if p1 and len(p1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return cleaned_data


class ProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={
        'class': INPUT_CLASSES, 'placeholder': 'First name'
    }))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={
        'class': INPUT_CLASSES, 'placeholder': 'Last name'
    }))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={
        'class': INPUT_CLASSES, 'placeholder': '98XXXXXXXX'
    }))
    avatar = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={
        'class': 'block w-full text-sm text-gray-600'
    }))

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip().replace(' ', '').replace('-', '')
        if not NEPALI_PHONE_REGEX.match(phone):
            raise forms.ValidationError(
                "Enter a valid 10-digit Nepali mobile number starting with 97 or 98."
            )
        return phone
