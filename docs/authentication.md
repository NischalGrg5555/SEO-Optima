# Authentication (step-by-step)

Purpose
- Describe how authentication (registration, login, OTP/verification, password reset) is implemented and how to reproduce or extend it.

Files involved
- [accounts/models.py](accounts/models.py)
- [accounts/forms.py](accounts/forms.py)
- [accounts/views.py](accounts/views.py)
- [accounts/urls.py](accounts/urls.py)
- templates/accounts/* (login, register, verify_otp, password reset)

Prerequisites
1. Virtualenv activated and project dependencies installed.
2. Database migrated: `python manage.py migrate`.

Step-by-step implementation
1. Models
   - Add/extend `User` or `UserProfile` in `accounts/models.py` to store profile fields (phone, otp, is_verified, profile_photo, brand_client_name, etc.).
2. Forms
   - Create `RegistrationForm`, `LoginForm`, `OTPVerifyForm`, `PasswordResetForm` in `accounts/forms.py` to validate input and perform any normalization (lowercase emails, strip whitespace).
3. URLs
   - Register auth endpoints in `accounts/urls.py` and include them in project `config/urls.py`.
4. Views
   - Implement `register`, `login_view`, `logout_view`, `verify_otp`, `password_reset` in `accounts/views.py`.
   - Use Django's `auth` utilities for login/logout and `django.contrib.auth.tokens` for password reset tokens where appropriate.
   - For OTP flow: generate an OTP, save it to the user profile with an expiry timestamp, send via email/SMS, and verify in `verify_otp`.
5. Templates
   - Provide accessible templates under `templates/accounts/` for each step (forms should post to the correct named URL).
6. Signals and post-registration hooks
   - Optionally use `signals.post_save` to create related profile records or enqueue welcome emails.
7. Tests
   - Add unit tests in `accounts/tests.py` for registration, login, OTP verification, and password reset flows.
8. Security
   - Ensure password hashing uses Django default, enforce strong passwords via validators, rate-limit OTP requests, and use HTTPS in production.

How to run locally
```
source .venv/bin/activate
python manage.py migrate
python manage.py runserver
```

Extending
- To add social login, integrate `django-allauth` or `python-social-auth` and map additional fields into `UserProfile`.

Notes
- Refer to existing views and templates in `accounts/` for concrete examples.
