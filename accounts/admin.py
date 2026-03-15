from django.contrib import admin
from .models import OTP, UserProfile

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'expires_at', 'is_verified')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('user__email', 'code')
    readonly_fields = ('created_at', 'expires_at')
    ordering = ('-created_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'job_title', 'timezone', 'receive_report_emails', 'receive_alert_emails')
    list_filter = ('receive_report_emails', 'receive_alert_emails', 'timezone')
    search_fields = ('user__email', 'user__first_name', 'company', 'job_title', 'default_property')

