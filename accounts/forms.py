from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

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

