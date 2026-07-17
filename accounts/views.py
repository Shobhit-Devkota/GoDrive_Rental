from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetCodeForm, ProfileEditForm
from .models import PasswordResetCode


def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully. Welcome to GoRental.")
            return redirect('core:home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        next_url = request.POST.get('next', '')
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                return redirect(next_url or 'core:home')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('core:home')


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            user = User.objects.get(email__iexact=form.cleaned_data['email'])
            reset_code = PasswordResetCode.generate_for_user(user)

            send_mail(
                subject="Your GoRental password reset code",
                message=(
                    f"Hi {user.username},\n\n"
                    f"Your password reset code is: {reset_code.code}\n\n"
                    f"This code expires in {PasswordResetCode.CODE_VALID_MINUTES} minutes. "
                    f"If you didn't request this, you can safely ignore this email.\n\n"
                    f"- GoRental"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            request.session['reset_user_id'] = user.pk
            messages.success(request, "A 6-digit reset code has been sent to your email.")
            return redirect('accounts:reset_code')
    else:
        form = ForgotPasswordForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_code_view(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, "Please start the password reset process again.")
        return redirect('accounts:forgot_password')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, "Please start the password reset process again.")
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        form = ResetCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code'].strip()
            reset_code = PasswordResetCode.objects.filter(
                user=user, code=code
            ).order_by('-created_at').first()

            if not reset_code or not reset_code.is_valid:
                messages.error(request, "That code is invalid or has expired. Please request a new one.")
                return redirect('accounts:forgot_password')

            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            reset_code.used = True
            reset_code.save()
            del request.session['reset_user_id']

            messages.success(request, "Your password has been reset. Please log in.")
            return redirect('accounts:login')
    else:
        form = ResetCodeForm()

    return render(request, 'accounts/reset_code.html', {'form': form, 'email': user.email})


@login_required
def profile_view(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'phone': profile.phone,
        })
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()

            profile.phone = form.cleaned_data['phone']
            if form.cleaned_data.get('avatar'):
                profile.avatar = form.cleaned_data['avatar']
            profile.save()

            messages.success(request, "Your profile has been updated.")
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'phone': profile.phone,
        })

    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})
