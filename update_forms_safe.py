#!/usr/bin/env python3
import os
import sys

os.chdir("/Users/nischalgurung/Desktop/Seo-optima v3")

# Read current forms
with open("dashboard/forms.py", "r") as f:
    current = f.read()

# Check if already exists
if "PDFReportGeneratorForm" in current:
    print("Forms already added!")
    sys.exit(0)

# Forms code
new_forms = """

class PDFReportGeneratorForm(forms.Form):
    \"\"\"Form for generating PDF reports\"\"\"
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
            'placeholder': 'e.g., February 2026 Website Analysis',
        })
    )
    
    description = forms.CharField(
        label='Report Description (Optional)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add any notes about this report...',
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
        label='Include Image & Alt Text Analysis',
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
        label='Include Visual Charts',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )


class PDFReportFilterForm(forms.Form):
    \"\"\"Form for filtering PDF reports\"\"\"
    sort_by = forms.ChoiceField(
        label='Sort By',
        required=False,
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('title', 'Title (A-Z)'),
            ('-title', 'Title (Z-A)'),
        ],
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    report_type = forms.ChoiceField(
        label='Report Type',
        required=False,
        choices=[
            ('', 'All Reports'),
            ('free', 'Free Reports Only'),
            ('paid', 'Premium Reports Only'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
"""

# Append to file
with open("dashboard/forms.py", "a") as f:
    f.write(new_forms)

print("Forms added successfully!")
