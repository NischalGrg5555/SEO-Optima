from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from .views import RegisterView, LoginViewCustom, logout_view, OTPVerifyView, ResendOTPView, GoogleLoginView, GoogleSignUpView, GoogleCallbackView, ProfileView, SettingsView
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

app_name = "accounts"

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("settings/", SettingsView.as_view(), name="settings"),
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", OTPVerifyView.as_view(), name="verify_otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend_otp"),
    path("google-login/", GoogleLoginView.as_view(), name="google_login"),
    path("google-signup/", GoogleSignUpView.as_view(), name="google_signup"),
    path("google-callback/", GoogleCallbackView.as_view(), name="google_callback"),
    path("login/", LoginViewCustom.as_view(), name="login"),
    path(
        "forgot-password/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            form_class=CustomPasswordResetForm,
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "forgot-password/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            form_class=CustomSetPasswordForm,
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("logout/", logout_view, name="logout"),
]


