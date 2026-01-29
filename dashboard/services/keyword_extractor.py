"""
Service to extract keywords and ranking data from Google Search Console
"""
import random
from typing import List, Dict, Optional
from urllib.parse import urlparse
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def fetch_gsc_keywords(url: str, credentials_dict: dict, days: int = 90) -> List[Dict[str, any]]:
    """
    Fetch real keyword data from Google Search Console API
    
    Args:
        url: The URL/property to fetch keywords for
        credentials_dict: OAuth2 credentials as dictionary
        days: Number of days of data to fetch (default: 90)
        
    Returns:
        List of dictionaries containing keyword data
    """
    try:
        # Create credentials object from dictionary
        credentials = Credentials(
            token=credentials_dict.get('token'),
            refresh_token=credentials_dict.get('refresh_token'),
            token_uri=credentials_dict.get('token_uri'),
            client_id=credentials_dict.get('client_id'),
            client_secret=credentials_dict.get('client_secret'),
            scopes=credentials_dict.get('scopes', ['https://www.googleapis.com/auth/webmasters.readonly'])
        )
        
        # Build the Search Console service
        service = build('searchconsole', 'v1', credentials=credentials)
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Prepare the request
        request = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'dimensions': ['query', 'page'],
            'rowLimit': 100,  # Get top 100 keywords
            'startRow': 0
        }
        
        # Execute the request
        response = service.searchanalytics().query(
            siteUrl=url,
            body=request
        ).execute()
        
        keywords_data = []
        
        if 'rows' in response:
            for row in response['rows']:
                keyword = row['keys'][0]  # query
                ranked_url = row['keys'][1] if len(row['keys']) > 1 else url  # page
                
                # Get metrics
                clicks = int(row.get('clicks', 0))
                impressions = int(row.get('impressions', 0))
                ctr = float(row.get('ctr', 0))
                position = round(float(row.get('position', 0)), 1)
                
                keywords_data.append({
                    'keyword': keyword,
                    'volume': impressions,  # Using impressions as volume
                    'position': position,
                    'url': ranked_url,
                    'clicks': clicks,
                    'ctr': round(ctr * 100, 2)  # Convert to percentage
                })
        
        # Sort by impressions (volume) descending
        keywords_data.sort(key=lambda x: x['volume'], reverse=True)
        
        return keywords_data
        
    except Exception as e:
        raise Exception(f"Error fetching from Google Search Console: {str(e)}")


def generate_mock_keywords(url: str) -> List[Dict[str, any]]:
    """
    Generate mock keyword data for demonstration
    Used when Google Search Console is not connected
    
    Args:
        url: The URL to generate keywords for
        
    Returns:
        List of dictionaries containing keyword data
    """
    
    # Parse the domain from URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc or parsed_url.path
    base_domain = domain.replace('www.', '')
    
    # Generate mock keywords based on common patterns
    mock_keyword_templates = [
        "{domain} reviews",
        "what is {domain}",
        "{domain} pricing",
        "{domain} features",
        "{domain} tutorial",
        "how to use {domain}",
        "{domain} vs competitors",
        "{domain} guide",
        "best {domain} practices",
        "{domain} tips",
        "{domain} alternatives",
        "{domain} comparison",
        "{domain} free trial",
        "{domain} discount",
        "{domain} coupon",
        "is {domain} worth it",
        "{domain} benefits",
        "{domain} pros and cons",
        "{domain} demo",
        "{domain} getting started",
        "{domain} documentation",
        "{domain} support",
        "{domain} login",
        "{domain} sign up",
        "{domain} download",
    ]
    
    # Generate random number of keywords (between 15-30)
    num_keywords = random.randint(15, 30)
    keywords_data = []
    
    # Extract domain name for keyword generation
    domain_name = base_domain.split('.')[0] if '.' in base_domain else base_domain
    
    for i in range(num_keywords):
        # Select random template
        template = random.choice(mock_keyword_templates)
        keyword = template.format(domain=domain_name)
        
        # Generate realistic-looking data
        volume = random.choice([10, 20, 30, 50, 70, 90, 100, 150, 200, 250, 300, 500, 1000, 2500, 5000])
        position = random.randint(1, 25)
        
        # Generate URL variations
        url_paths = [
            url,
            f"{url}/blog",
            f"{url}/blog/{keyword.replace(' ', '-')}",
            f"{url}/features",
            f"{url}/pricing",
            f"{url}/about",
            f"{url}/docs",
            f"{url}/guides/{keyword.replace(' ', '-')}",
        ]
        
        ranked_url = random.choice(url_paths)
        
        keywords_data.append({
            'keyword': keyword,
            'volume': volume,
            'position': position,
            'url': ranked_url,
        })
    
    # Sort by volume (descending)
    keywords_data.sort(key=lambda x: x['volume'], reverse=True)
    
    return keywords_data


def get_keyword_stats(keywords: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Calculate statistics from keyword data
    
    Args:
        keywords: List of keyword dictionaries
        
    Returns:
        Dictionary with keyword statistics
    """
    total_keywords = len(keywords)
    
    # Count keywords in different position ranges
    top_3 = sum(1 for k in keywords if k['position'] <= 3)
    top_10 = sum(1 for k in keywords if k['position'] <= 10)
    top_20 = sum(1 for k in keywords if k['position'] <= 20)
    
    # Calculate total search volume
    total_volume = sum(k['volume'] for k in keywords)
    
    # Average position
    avg_position = sum(k['position'] for k in keywords) / total_keywords if total_keywords > 0 else 0
    
    # Total clicks (if available)
    total_clicks = sum(k.get('clicks', 0) for k in keywords)
    
    return {
        'total_keywords': total_keywords,
        'top_3_positions': top_3,
        'top_10_positions': top_10,
        'top_20_positions': top_20,
        'total_volume': total_volume,
        'avg_position': round(avg_position, 1),
        'total_clicks': total_clicks,
    }
