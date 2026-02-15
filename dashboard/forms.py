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

class KeywordsFinderForm(forms.Form):
    """Form for finding keywords for a website"""
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


class PDFReportGeneratorForm(forms.Form):
    """Form for generating PDF reports from analysis data"""
    
    REPORT_TYPE_CHOICES = [
        ('free', 'Free Report - Basic Summary'),
        ('paid', 'Premium Report - Comprehensive Analysis'),
    ]
    
    report_type = forms.ChoiceField(
        label='Report Type',
        choices=REPORT_TYPE_CHOICES,
        initial='free',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )
    
    title = forms.CharField(
        label='Report Title',
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., SEO Analysis - February 2026',
        })
    )
    
    description = forms.CharField(
        label='Description (Optional)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Add notes or context about this report...',
            'rows': 3,
        })
    )
    
    include_pagespeed = forms.BooleanField(
        label='Include Page Speed Analysis',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    include_keywords = forms.BooleanField(
        label='Include Keywords Analysis',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    include_images = forms.BooleanField(
        label='Include Image Alt Text Analysis',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    include_headers = forms.BooleanField(
        label='Include Headers Analysis',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    include_recommendations = forms.BooleanField(
        label='Include Recommendations',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    include_charts = forms.BooleanField(
        label='Include Charts and Visualizations',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    pagespeed_analysis = forms.IntegerField(
        label='PageSpeed Analysis',
        required=False,
        widget=forms.HiddenInput()
    )
    
    keyword_analysis = forms.IntegerField(
        label='Keyword Analysis',
        required=False,
        widget=forms.HiddenInput()
    )
    
    image_analysis = forms.IntegerField(
        label='Image Analysis',
        required=False,
        widget=forms.HiddenInput()
    )


class PDFReportFilterForm(forms.Form):
    """Form for filtering and sorting PDF reports"""
    
    SORT_CHOICES = [
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
        ('title', 'Title (A-Z)'),
        ('-title', 'Title (Z-A)'),
    ]
    
    REPORT_TYPE_CHOICES = [
        ('', 'All Reports'),
        ('free', 'Free Reports'),
        ('paid', 'Premium Reports'),
    ]
    
    report_type = forms.ChoiceField(
        label='Report Type',
        required=False,
        choices=REPORT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    sort_by = forms.ChoiceField(
        label='Sort By',
        required=False,
        choices=SORT_CHOICES,
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )