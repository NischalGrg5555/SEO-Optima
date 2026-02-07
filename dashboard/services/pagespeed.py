import requests
import os
from django.conf import settings

PAGESPEED_API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def get_pagespeed_api_key():
    """Get API key from environment"""
    return os.environ.get('PAGESPEED_API_KEY', settings.PAGESPEED_API_KEY)


def fetch_pagespeed_data(url: str, strategy="mobile"):
    """
    Fetch PageSpeed Insights data for a given URL
    
    Args:
        url: Website URL to analyze
        strategy: 'mobile' or 'desktop'
    
    Returns:
        dict with analysis results
    """
    api_key = get_pagespeed_api_key()
    
    if not api_key or api_key == 'your-google-pagespeed-api-key':
        raise ValueError(
            "PageSpeed API key not configured. "
            "Please get an API key from Google Cloud Console and add it to .env"
        )
    
    params = {
        "url": url,
        "strategy": strategy,
        "key": api_key,
        "category": ["performance", "accessibility", "best-practices", "seo"],
    }
    
    try:
        response = requests.get(PAGESPEED_API, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        return parse_pagespeed_response(data)
    
    except requests.exceptions.Timeout:
        raise Exception("Request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching PageSpeed data: {str(e)}")


def parse_pagespeed_response(response: dict) -> dict:
    """
    Parse Google PageSpeed Insights API response
    
    Returns:
        dict with formatted metrics
    """
    try:
        lighthouse = response.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        audits = lighthouse.get("audits", {})
        
        # Extract scores
        scores = {
            'performance': categories.get('performance', {}).get('score'),
            'accessibility': categories.get('accessibility', {}).get('score'),
            'best_practices': categories.get('best-practices', {}).get('score'),
            'seo': categories.get('seo', {}).get('score'),
        }
        
        # Convert to 0-100 scale
        for key in scores:
            if scores[key] is not None:
                scores[key] = int(scores[key] * 100)
        
        # Extract key metrics
        metrics = {}
        
        # First Contentful Paint (FCP)
        if 'first-contentful-paint' in audits:
            metrics['fcp'] = {
                'title': 'First Contentful Paint',
                'value': audits['first-contentful-paint'].get('displayValue', 'N/A'),
                'score': audits['first-contentful-paint'].get('score'),
            }
        
        # Speed Index
        if 'speed-index' in audits:
            metrics['speed_index'] = {
                'title': 'Speed Index',
                'value': audits['speed-index'].get('displayValue', 'N/A'),
                'score': audits['speed-index'].get('score'),
            }
        
        # Largest Contentful Paint (LCP)
        if 'largest-contentful-paint' in audits:
            metrics['lcp'] = {
                'title': 'Largest Contentful Paint',
                'value': audits['largest-contentful-paint'].get('displayValue', 'N/A'),
                'score': audits['largest-contentful-paint'].get('score'),
            }
        
        # Total Blocking Time (TBT)
        if 'total-blocking-time' in audits:
            metrics['tbt'] = {
                'title': 'Total Blocking Time',
                'value': audits['total-blocking-time'].get('displayValue', 'N/A'),
                'score': audits['total-blocking-time'].get('score'),
            }
        
        # Cumulative Layout Shift (CLS)
        if 'cumulative-layout-shift' in audits:
            metrics['cls'] = {
                'title': 'Cumulative Layout Shift',
                'value': audits['cumulative-layout-shift'].get('displayValue', 'N/A'),
                'score': audits['cumulative-layout-shift'].get('score'),
            }
        
        # Extract Field Data (Real User Data from Chrome UX Report)
        field_data = {}
        loading_experience = response.get('loadingExperience', {})
        origin_loading_experience = response.get('originLoadingExperience', {})
        
        # Use origin data if available, otherwise use URL-specific data
        experience_data = origin_loading_experience if origin_loading_experience else loading_experience
        
        if experience_data and 'metrics' in experience_data:
            field_metrics = experience_data['metrics']
            
            # Overall assessment
            field_data['overall_category'] = experience_data.get('overall_category', 'UNKNOWN')
            
            # Largest Contentful Paint (LCP) - Field Data
            if 'LARGEST_CONTENTFUL_PAINT_MS' in field_metrics:
                lcp_data = field_metrics['LARGEST_CONTENTFUL_PAINT_MS']
                field_data['field_lcp'] = {
                    'title': 'Largest Contentful Paint (LCP)',
                    'value': format_field_value(lcp_data.get('percentile'), 'ms'),
                    'category': lcp_data.get('category', 'UNKNOWN'),
                    'percentile': lcp_data.get('percentile'),
                    'distributions': lcp_data.get('distributions', [])
                }
            
            # Interaction to Next Paint (INP) - Field Data
            if 'INTERACTION_TO_NEXT_PAINT' in field_metrics:
                inp_data = field_metrics['INTERACTION_TO_NEXT_PAINT']
                field_data['field_inp'] = {
                    'title': 'Interaction to Next Paint (INP)',
                    'value': format_field_value(inp_data.get('percentile'), 'ms'),
                    'category': inp_data.get('category', 'UNKNOWN'),
                    'percentile': inp_data.get('percentile'),
                    'distributions': inp_data.get('distributions', [])
                }
            
            # Cumulative Layout Shift (CLS) - Field Data
            if 'CUMULATIVE_LAYOUT_SHIFT_SCORE' in field_metrics:
                cls_data = field_metrics['CUMULATIVE_LAYOUT_SHIFT_SCORE']
                field_data['field_cls'] = {
                    'title': 'Cumulative Layout Shift (CLS)',
                    'value': format_cls_value(cls_data.get('percentile')),
                    'category': cls_data.get('category', 'UNKNOWN'),
                    'percentile': cls_data.get('percentile'),
                    'distributions': cls_data.get('distributions', [])
                }
            
            # First Contentful Paint (FCP) - Field Data
            if 'FIRST_CONTENTFUL_PAINT_MS' in field_metrics:
                fcp_data = field_metrics['FIRST_CONTENTFUL_PAINT_MS']
                field_data['field_fcp'] = {
                    'title': 'First Contentful Paint (FCP)',
                    'value': format_field_value(fcp_data.get('percentile'), 'ms'),
                    'category': fcp_data.get('category', 'UNKNOWN'),
                    'percentile': fcp_data.get('percentile'),
                    'distributions': fcp_data.get('distributions', [])
                }
            
            # First Input Delay / Time to First Byte
            if 'EXPERIMENTAL_TIME_TO_FIRST_BYTE' in field_metrics:
                ttfb_data = field_metrics['EXPERIMENTAL_TIME_TO_FIRST_BYTE']
                field_data['field_ttfb'] = {
                    'title': 'Time to First Byte (TTFB)',
                    'value': format_field_value(ttfb_data.get('percentile'), 'ms'),
                    'category': ttfb_data.get('category', 'UNKNOWN'),
                    'percentile': ttfb_data.get('percentile'),
                    'distributions': ttfb_data.get('distributions', [])
                }
        
        return {
            'scores': scores,
            'metrics': metrics,
            'field_data': field_data,
            'full_response': response,
        }
    
    except Exception as e:
        raise Exception(f"Error parsing PageSpeed response: {str(e)}")


def get_score_color(score):
    """Get color for score badge"""
    if score is None:
        return 'secondary'
    score = int(score)
    if score >= 90:
        return 'success'  # Green
    elif score >= 50:
        return 'warning'  # Orange
    else:
        return 'danger'   # Red


def get_metric_status(score):
    """Get status for metric"""
    if score is None:
        return 'Unknown'
    score = float(score)
    if score >= 0.9:
        return 'Good'
    elif score >= 0.5:
        return 'Needs Work'
    else:
        return 'Poor'


def format_field_value(value, unit='ms'):
    """Format field data value for display"""
    if value is None:
        return 'N/A'
    
    if unit == 'ms':
        # Convert to seconds if > 1000ms
        if value >= 1000:
            return f"{value / 1000:.1f} s"
        return f"{value} ms"
    
    return str(value)


def format_cls_value(value):
    """Format CLS value (it's already a decimal)"""
    if value is None:
        return 'N/A'
    # CLS values are between 0 and 1, display with 2 decimal places
    return f"{value / 100:.2f}" if value > 1 else f"{value:.2f}"


def get_field_category_badge(category):
    """Convert Chrome UX Report category to badge class"""
    category_map = {
        'FAST': 'good',
        'AVERAGE': 'fair',
        'SLOW': 'poor',
        'UNKNOWN': 'secondary'
    }
    return category_map.get(category, 'secondary')


def extract_field_data_from_response(response):
    """
    Extract field data from a stored PageSpeed API response
    Used for displaying field data in analysis detail view
    """
    field_data = {}
    
    if not response:
        return field_data
    
    loading_experience = response.get('loadingExperience', {})
    origin_loading_experience = response.get('originLoadingExperience', {})
    
    # Use origin data if available, otherwise use URL-specific data
    experience_data = origin_loading_experience if origin_loading_experience else loading_experience
    
    if experience_data and 'metrics' in experience_data:
        field_metrics = experience_data['metrics']
        
        # Overall assessment
        field_data['overall_category'] = experience_data.get('overall_category', 'UNKNOWN')
        
        # Largest Contentful Paint (LCP) - Field Data
        if 'LARGEST_CONTENTFUL_PAINT_MS' in field_metrics:
            lcp_data = field_metrics['LARGEST_CONTENTFUL_PAINT_MS']
            field_data['field_lcp'] = {
                'title': 'Largest Contentful Paint (LCP)',
                'value': format_field_value(lcp_data.get('percentile'), 'ms'),
                'category': lcp_data.get('category', 'UNKNOWN'),
                'percentile': lcp_data.get('percentile'),
                'distributions': lcp_data.get('distributions', [])
            }
        
        # Interaction to Next Paint (INP) - Field Data
        if 'INTERACTION_TO_NEXT_PAINT' in field_metrics:
            inp_data = field_metrics['INTERACTION_TO_NEXT_PAINT']
            field_data['field_inp'] = {
                'title': 'Interaction to Next Paint (INP)',
                'value': format_field_value(inp_data.get('percentile'), 'ms'),
                'category': inp_data.get('category', 'UNKNOWN'),
                'percentile': inp_data.get('percentile'),
                'distributions': inp_data.get('distributions', [])
            }
        
        # Cumulative Layout Shift (CLS) - Field Data
        if 'CUMULATIVE_LAYOUT_SHIFT_SCORE' in field_metrics:
            cls_data = field_metrics['CUMULATIVE_LAYOUT_SHIFT_SCORE']
            field_data['field_cls'] = {
                'title': 'Cumulative Layout Shift (CLS)',
                'value': format_cls_value(cls_data.get('percentile')),
                'category': cls_data.get('category', 'UNKNOWN'),
                'percentile': cls_data.get('percentile'),
                'distributions': cls_data.get('distributions', [])
            }
        
        # First Contentful Paint (FCP) - Field Data
        if 'FIRST_CONTENTFUL_PAINT_MS' in field_metrics:
            fcp_data = field_metrics['FIRST_CONTENTFUL_PAINT_MS']
            field_data['field_fcp'] = {
                'title': 'First Contentful Paint (FCP)',
                'value': format_field_value(fcp_data.get('percentile'), 'ms'),
                'category': fcp_data.get('category', 'UNKNOWN'),
                'percentile': fcp_data.get('percentile'),
                'distributions': fcp_data.get('distributions', [])
            }
        
        # Time to First Byte
        if 'EXPERIMENTAL_TIME_TO_FIRST_BYTE' in field_metrics:
            ttfb_data = field_metrics['EXPERIMENTAL_TIME_TO_FIRST_BYTE']
            field_data['field_ttfb'] = {
                'title': 'Time to First Byte (TTFB)',
                'value': format_field_value(ttfb_data.get('percentile'), 'ms'),
                'category': ttfb_data.get('category', 'UNKNOWN'),
                'percentile': ttfb_data.get('percentile'),
                'distributions': ttfb_data.get('distributions', [])
            }
    
    return field_data
