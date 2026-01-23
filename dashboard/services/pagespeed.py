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
        
        return {
            'scores': scores,
            'metrics': metrics,
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


    return {
        "performance_score": round(categories["performance"]["score"] * 100),

        # Core Web Vitals (real SEO value)
        "lcp": audits["largest-contentful-paint"]["displayValue"],
        "cls": audits["cumulative-layout-shift"]["displayValue"],
        "inp": audits["interaction-to-next-paint"]["displayValue"],
    }
