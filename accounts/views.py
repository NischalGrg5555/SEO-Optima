from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, FormView
from django.views import View
from django.core.mail import send_mail
from django.http import JsonResponse
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import json
import requests

from .forms import RegisterForm, LoginForm, OTPVerifyForm
from .models import OTP

class RegisterView(CreateView):
    template_name = "accounts/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("accounts:verify_otp")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['google_client_id'] = settings.GOOGLE_CLIENT_ID
        return context

    def form_valid(self, form):
        # Save user (inactive)
        user = form.save()
        
        # Generate OTP
        otp = OTP.create_otp(user)
        
        # Print OTP to console for development
        print(f"\n{'='*50}")
        print(f"🔐 OTP GENERATED FOR: {user.email}")
        print(f"🔑 CODE: {otp.code}")
        print(f"⏰ EXPIRES AT: {otp.expires_at}")
        print(f"{'='*50}\n")
        
        # Send OTP via email (console backend for development)
        try:
            send_mail(
                subject='Your OTP Code - SEO Optima',
                message=f'Your OTP code is: {otp.code}\n\nThis code will expire in 10 minutes.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            messages.success(self.request, f"Registration successful! OTP sent to {user.email}")
        except Exception as e:
            messages.warning(self.request, f"Account created but couldn't send OTP. Your code is: {otp.code}")
        
        # Store user ID in session for OTP verification
        self.request.session['otp_user_id'] = user.id
        self.request.session['otp_action'] = 'register'
        
        return redirect(self.success_url)


class OTPVerifyView(FormView):
    template_name = "accounts/verify_otp.html"
    form_class = OTPVerifyForm
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        # Check if user_id exists in session
        if 'otp_user_id' not in request.session:
            messages.error(request, "Invalid session. Please register again.")
            return redirect('accounts:register')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.session.get('otp_user_id')
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            context['user_email'] = user.email
        except User.DoesNotExist:
            pass
        return context

    def form_valid(self, form):
        user_id = self.request.session.get('otp_user_id')
        otp_code = form.cleaned_data['otp']
        
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            
            # Get the latest OTP for this user
            otp = user.otps.filter(is_verified=False).order_by('-created_at').first()
            
            # Debug logging
            print(f"\n{'='*50}")
            print(f"🔍 OTP VERIFICATION ATTEMPT")
            print(f"📧 User: {user.email}")
            print(f"🔑 Entered Code: '{otp_code}'")
            print(f"✅ Expected Code: '{otp.code if otp else 'N/A'}'")
            print(f"⏰ Expired: {otp.is_expired() if otp else 'N/A'}")
            print(f"{'='*50}\n")
            
            if not otp:
                messages.error(self.request, "No OTP found. Please register again.")
                return redirect('accounts:register')
            
            if otp.is_expired():
                messages.error(self.request, "OTP has expired. Please request a new one.")
                return self.form_invalid(form)
            
            if otp.code != otp_code:
                messages.error(self.request, "Invalid OTP code. Please try again.")
                return self.form_invalid(form)
            
            # Verify OTP
            otp.is_verified = True
            otp.save()
            
            # Activate user
            user.is_active = True
            user.save()

            # Clear session
            action = self.request.session.get('otp_action', 'register')
            del self.request.session['otp_user_id']
            self.request.session.pop('otp_action', None)

            if action == 'google_login':
                login(self.request, user)
                messages.success(self.request, "Signed in with Google after OTP verification.")
                return redirect('core:home')

            if action == 'google_signup':
                login(self.request, user)
                messages.success(self.request, "Account created and verified! Welcome to SEO Optima.")
                return redirect('core:home')

            messages.success(self.request, "Email verified successfully! You can now sign in.")
            return redirect(self.success_url)
            
        except User.DoesNotExist:
            messages.error(self.request, "User not found.")
            return redirect('accounts:register')


class ResendOTPView(View):
    def post(self, request):
        user_id = request.session.get('otp_user_id')
        
        if not user_id:
            messages.error(request, "Invalid session. Please register again.")
            return redirect('accounts:register')
        
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            
            # Generate new OTP
            otp = OTP.create_otp(user)
            
            # Send OTP via email
            try:
                send_mail(
                    subject='Your OTP Code - SEO Optima',
                    message=f'Your new OTP code is: {otp.code}\n\nThis code will expire in 10 minutes.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, "New OTP sent to your email!")
            except Exception as e:
                messages.warning(request, f"Couldn't send OTP. Your code is: {otp.code}")
            
            return redirect('accounts:verify_otp')
            
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('accounts:register')


class LoginViewCustom(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Invalid credentials. Please try again.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['google_client_id'] = settings.GOOGLE_CLIENT_ID
        return context


class GoogleLoginView(View):
    def get(self, request):
        """Redirect to Google OAuth login"""
        import os
        import secrets

        client_id = settings.GOOGLE_CLIENT_ID
        if not client_id:
            messages.error(request, "Google OAuth not configured on server.")
            return redirect('accounts:login')

        # Get the protocol and host
        protocol = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        redirect_uri = f"{protocol}://{host}/accounts/google-callback/"

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        request.session['google_oauth_state'] = state
        request.session['google_redirect_uri'] = redirect_uri

        # Build Google OAuth URL
        from urllib.parse import urlencode
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
        }
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

        return redirect(google_auth_url)


class GoogleSignUpView(View):
    def get(self, request):
        """Redirect to Google OAuth for signup"""
        import os
        import secrets

        client_id = settings.GOOGLE_CLIENT_ID
        if not client_id:
            messages.error(request, "Google OAuth not configured on server.")
            return redirect('accounts:register')

        # Get the protocol and host
        protocol = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        redirect_uri = f"{protocol}://{host}/accounts/google-callback/"

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        request.session['google_oauth_state'] = state
        request.session['google_redirect_uri'] = redirect_uri
        request.session['google_action'] = 'signup'  # Mark this as a signup action

        # Build Google OAuth URL
        from urllib.parse import urlencode
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
        }
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

        return redirect(google_auth_url)


class GoogleCallbackView(View):
    def get(self, request):
        """Handle OAuth callback from Google"""
        import os

        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')

        if error:
            messages.error(request, f"Google authentication failed: {error}")
            return redirect('accounts:login')

        if not code:
            messages.error(request, "No authorization code received from Google.")
            return redirect('accounts:login')

        # Verify state
        session_state = request.session.get('google_oauth_state')
        if not session_state or state != session_state:
            messages.error(request, "State mismatch. Please try again.")
            return redirect('accounts:login')

        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
        redirect_uri = request.session.get('google_redirect_uri')

        if not client_id or not client_secret or not redirect_uri:
            messages.error(request, "Server not properly configured for Google login.")
            return redirect('accounts:login')

        try:
            # Exchange code for token
            token_url = 'https://oauth2.googleapis.com/token'
            token_data = {
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }

            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            token_response = response.json()

            id_token_jwt = token_response.get('id_token')
            if not id_token_jwt:
                messages.error(request, "No ID token received from Google.")
                return redirect('accounts:login')

            # Verify and decode the ID token
            idinfo = id_token.verify_oauth2_token(id_token_jwt, google_requests.Request(), client_id)

            email = idinfo.get('email')
            email_verified = idinfo.get('email_verified')
            name = idinfo.get('name') or (email.split('@')[0] if email else "")

            if not email or not email_verified:
                messages.error(request, "Google account email not verified.")
                return redirect('accounts:login')

            # Create or update user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": name,
                    "is_active": False,
                }
            )

            if created:
                user.set_unusable_password()
            else:
                user.first_name = user.first_name or name
                user.is_active = False
            user.save()

            # Generate and send OTP
            otp = OTP.create_otp(user)
            try:
                send_mail(
                    subject='Your OTP Code - SEO Optima (Google Sign-In)',
                    message=f'Your OTP code is: {otp.code}\n\nThis code will expire in 10 minutes.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                messages.warning(request, f"Account created but OTP email failed: {str(e)}")

            # Clean up session
            request.session['otp_user_id'] = user.id
            
            # Check if this was a signup action
            google_action = request.session.pop('google_action', 'login')
            if google_action == 'signup':
                request.session['otp_action'] = 'google_signup'
            else:
                request.session['otp_action'] = 'google_login'
            
            request.session.pop('google_oauth_state', None)
            request.session.pop('google_redirect_uri', None)

            messages.success(request, f"OTP sent to {email}")
            return redirect('accounts:verify_otp')

        except Exception as e:
            messages.error(request, f"Google authentication failed: {str(e)}")
            return redirect('accounts:login')



def logout_view(request):
    logout(request)
    return redirect("accounts:login")

