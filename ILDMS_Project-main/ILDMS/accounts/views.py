# accounts/views.py
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.conf import settings
import secrets
from datetime import datetime, timedelta
from .forms import ProfileUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from .forms import (
    UserRegistrationForm,
    CustomLoginForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    CustomPasswordChangeForm
)
from .models import EmailVerificationToken
from main.models import User
from django.views.generic import TemplateView
from .email_utils import send_verification_email_async, send_welcome_email_async 

class HomePageView(TemplateView):
    template_name = 'index.html'

class RegisterView(generic.CreateView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance

        # Create verification token
        verification = EmailVerificationToken.create_token(user)
        verification_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:verify_email', kwargs={'token': verification.token})
        )

        # Send verification email asynchronously (won't block registration)
        send_verification_email_async(user, verification_url)
        
        # Send welcome email asynchronously
        send_welcome_email_async(user)

        messages.success(
            self.request,
            'Registration successful! Please check your email to verify your account.'
        )
        return response


class VerifyEmailView(generic.View):
    def get(self, request, token):
        try:
            verification = EmailVerificationToken.objects.get(token=token)

            if verification.expires_at < datetime.now(verification.expires_at.tzinfo):
                messages.error(request, 'Verification link has expired.')
                return redirect('accounts:login')

            user = verification.user
            user.is_verified = True
            user.save()
            verification.delete()

            messages.success(request, 'Email verified successfully! You can now log in.')
            return redirect('accounts:login')

        except EmailVerificationToken.DoesNotExist:
            messages.error(request, 'Invalid verification link.')
            return redirect('accounts:login')


class CustomLoginView(auth_views.LoginView):
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_verified:
            messages.error(self.request, 'Please verify your email before logging in.')
            return redirect('accounts:login')
        return super().form_valid(form)

# class CustomLogoutView(LogoutView):
#     next_page = 'accounts:login'
#
#     def dispatch(self, request, *args, **kwargs):
#         if request.method.lower() == 'get':
#             # Force logout on GET (not secure for public apps)
#             messages.success(request, "You have been logged out.")
#             return self.get(request, *args, **kwargs)
#         return super().dispatch(request, *args, **kwargs)

class CustomPasswordResetView(auth_views.PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


class CustomPasswordChangeView(auth_views.PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')


class CustomPasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'

class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'

    def get_object(self):
        return self.request.user

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)