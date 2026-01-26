from django import forms
from .models import PageSpeedAnalysis

class PageSpeedForm(forms.Form):
    url = forms.URLField(
        label='Website URL',
        required=True,
        widget=forms.URLInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'https://example.com',
            'autocomplete': 'off',
        }),
        error_messages={
            'required': 'Please enter a valid website URL',
            'invalid': 'Please enter a valid URL (e.g., https://example.com)',
        }
    )
    
    strategy = forms.ChoiceField(
        label='Device Type',
        choices=[('mobile', 'Mobile'), ('desktop', 'Desktop')],
        initial='mobile',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )

class PageSpeedFilterForm(forms.Form):
    """Form for filtering PageSpeed analyses"""
    strategy = forms.ChoiceField(
        label='Device',
        required=False,
        choices=[('', 'All'), ('mobile', 'Mobile'), ('desktop', 'Desktop')],
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    sort_by = forms.ChoiceField(
        label='Sort By',
        required=False,
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('-performance_score', 'Performance (High to Low)'),
            ('performance_score', 'Performance (Low to High)'),
        ],
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )


class HeaderExtractorForm(forms.Form):
    """Form for extracting headers from a webpage"""
    url = forms.URLField(
        label='Website URL',
        required=True,
        widget=forms.URLInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'https://example.com',
            'autocomplete': 'off',
        }),
        error_messages={
            'required': 'Please enter a valid website URL',
            'invalid': 'Please enter a valid URL (e.g., https://example.com)',
        }
    )

class ImageAltFinderForm(forms.Form):
    """Form for extracting images and alt text from a webpage"""
    url = forms.URLField(
        label='Website URL',
        required=True,
        widget=forms.URLInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'https://example.com',
            'autocomplete': 'off',
        }),
        error_messages={
            'required': 'Please enter a valid website URL',
            'invalid': 'Please enter a valid URL (e.g., https://example.com)',
        }
    )