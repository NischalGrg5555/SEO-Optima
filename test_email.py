import os
from dotenv import load_dotenv
load_dotenv()

print("EMAIL_HOST_USER:", os.environ.get('EMAIL_HOST_USER'))
print("EMAIL_HOST_PASSWORD:", os.environ.get('EMAIL_HOST_PASSWORD'))

# Test Django email
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("\nEmail Backend:", settings.EMAIL_BACKEND)
print("EMAIL_HOST:", settings.EMAIL_HOST)
print("EMAIL_PORT:", settings.EMAIL_PORT)
print("EMAIL_USE_TLS:", settings.EMAIL_USE_TLS)
print("DEFAULT_FROM_EMAIL:", settings.DEFAULT_FROM_EMAIL)

try:
    result = send_mail(
        subject='Test OTP Email',
        message='This is a test OTP email\n\nTest code: 123456',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['nischalgrg2022@gmail.com'],
        fail_silently=False,
    )
except Exception as e:
    print(f"\n❌ Error sending email: {e}")
    import traceback
    traceback.print_exc()
