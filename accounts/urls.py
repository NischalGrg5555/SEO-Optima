from django.urls import path
from .views import RegisterView, LoginViewCustom, logout_view, OTPVerifyView, ResendOTPView, GoogleLoginView, GoogleSignUpView, GoogleCallbackView

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", OTPVerifyView.as_view(), name="verify_otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend_otp"),
    path("google-login/", GoogleLoginView.as_view(), name="google_login"),
    path("google-signup/", GoogleSignUpView.as_view(), name="google_signup"),
    path("google-callback/", GoogleCallbackView.as_view(), name="google_callback"),
    path("login/", LoginViewCustom.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
]


