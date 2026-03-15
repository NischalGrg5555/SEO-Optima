from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import UserProfile

class RegisterForm(UserCreationForm):
    name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": "Enter your name",
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        "class": "form-control",
        "placeholder": "Enter your email",
    }))

    class Meta:
        model = User
        fields = ("name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"].lower().strip()  # simple: username = email
        user.email = self.cleaned_data["email"].lower().strip()
        user.first_name = self.cleaned_data["name"].strip()
        user.is_active = False  # User will be activated after OTP verification
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": "Enter your email",
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "form-control",
        "placeholder": "Password",
    }))


class OTPVerifyForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control text-center",
            "placeholder": "Enter 6-digit OTP",
            "maxlength": "6",
            "pattern": "[0-9]{6}",
            "inputmode": "numeric"
        }),
        error_messages={
            'required': 'Please enter the OTP code.',
            'min_length': 'OTP must be 6 digits.',
            'max_length': 'OTP must be 6 digits.'
        }
    )


class PersonalInformationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Name',
    }))
    email = forms.EmailField(disabled=True, required=False, widget=forms.EmailInput(attrs={
        'class': 'form-control',
    }))

    class Meta:
        model = UserProfile
        fields = [
            'profile_photo',
            'facebook_url',
            'x_url',
            'linkedin_url',
            'instagram_url',
            'first_name',
            'email',
            'company',
            'job_title',
            'bio',
        ]
        widgets = {
            'profile_photo': forms.FileInput(attrs={'class': 'profile-v2-photo-input', 'accept': 'image/*'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.facebook.com/your-page'}),
            'x_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/your-handle'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/your-profile'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/your-handle'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO Analyst'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell people what you focus on.'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['first_name'].initial = user.get_full_name().strip() or user.first_name or user.username
        self.fields['email'].initial = user.email
        self.fields['profile_photo'].required = False

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data['first_name'].strip()
        self.user.last_name = ''
        if commit:
            self.user.save(update_fields=['first_name', 'last_name'])
            profile.user = self.user
            profile.save()
        return profile


class SettingsForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
        })
    )
    current_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current password',
        })
    )
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
        })
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['username'].initial = self.user.username
        if not self.user.has_usable_password():
            self.fields['current_password'].required = False

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password', '')
        if not self.user.has_usable_password():
            return current_password  # Google users have no password — skip check
        if not current_password:
            raise ValidationError('Current password is required.')
        if not self.user.check_password(current_password):
            raise ValidationError('Current password is incorrect.')
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password', '')
        confirm_password = cleaned_data.get('confirm_password', '')

        if new_password or confirm_password:
            if not new_password:
                self.add_error('new_password', 'Please enter a new password.')
            if not confirm_password:
                self.add_error('confirm_password', 'Please confirm your new password.')
            if new_password and confirm_password and new_password != confirm_password:
                self.add_error('confirm_password', 'New password and confirm password must match.')
            if new_password and new_password == confirm_password:
                validate_password(new_password, self.user)

        return cleaned_data

    def save(self):
        self.user.username = self.cleaned_data['username']
        if self.cleaned_data.get('new_password'):
            self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()
        return self.user

