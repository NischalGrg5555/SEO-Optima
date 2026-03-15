from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
import random


class UserProfile(models.Model):
    DATE_RANGE_CHOICES = [
        ('7d', 'Last 7 days'),
        ('28d', 'Last 28 days'),
        ('90d', 'Last 90 days'),
    ]
    DEVICE_CHOICES = [
        ('mobile', 'Mobile'),
        ('desktop', 'Desktop'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.CharField(max_length=150, blank=True)
    job_title = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    timezone = models.CharField(max_length=100, default='UTC')
    bio = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    facebook_url = models.URLField(blank=True)
    x_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    brand_client_name = models.CharField(max_length=150, blank=True)
    default_country = models.CharField(max_length=100, blank=True)
    default_device = models.CharField(max_length=10, choices=DEVICE_CHOICES, default='mobile')
    default_property = models.CharField(max_length=255, blank=True)
    preferred_date_range = models.CharField(max_length=10, choices=DATE_RANGE_CHOICES, default='28d')
    receive_report_emails = models.BooleanField(default=True)
    receive_alert_emails = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__email']

    def __str__(self):
        return f"Profile for {self.user.email}"

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.code}"
    
    @staticmethod
    def generate_code():
        """Generate a 6-digit OTP code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    def is_expired(self):
        """Check if OTP is expired"""
        return timezone.now() > self.expires_at
    
    @classmethod
    def create_otp(cls, user):
        """Create a new OTP for the user with 10 minutes expiry"""
        code = cls.generate_code()
        expires_at = timezone.now() + timedelta(minutes=10)
        return cls.objects.create(user=user, code=code, expires_at=expires_at)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        return

    UserProfile.objects.get_or_create(user=instance)
