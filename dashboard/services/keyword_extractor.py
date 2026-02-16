"""
Service to extract keywords and ranking data from Google Search Console
"""
import random
from typing import List, Dict, Optional
from urllib.parse import urlparse
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def fetch_gsc_keywords(url: str, credentials_dict: dict, properties_list: list = None, days: int = 90) -> List[Dict[str, any]]:
    """
    Fetch real keyword data from Google Search Console API
    
    Args:
        url: The URL/property to fetch keywords for
        credentials_dict: OAuth2 credentials as dictionary
        properties_list: List of available properties from GSC (for smart matching)
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
        
        # Generate different URL format variations to try, including domain properties
        url_variations = _generate_url_variations(url, properties_list)
        
        keywords_data = []
        last_error = None
        
        # Try each URL variation
        for site_url in url_variations:
            try:
                # Execute the request
                response = service.searchanalytics().query(
                    siteUrl=site_url,
                    body=request
                ).execute()
                
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
                    
                    # If we got data, sort and return
                    if keywords_data:
                        keywords_data.sort(key=lambda x: x['volume'], reverse=True)
                        return keywords_data
                    
            except Exception as e:
                last_error = str(e)
                continue
        
        # If no data found with any variation, raise the last error
        if not keywords_data and last_error:
            available_props = f"\n\nAvailable properties in your GSC account:\n" + \
                            "\n".join([f"  • {p}" for p in (properties_list or [])])
            raise Exception(f"Property not found in Google Search Console for '{url}'. Tried variations: {', '.join(url_variations)}. {available_props}\n\nLast error: {last_error}")
        
        # Sort by impressions (volume) descending
        keywords_data.sort(key=lambda x: x['volume'], reverse=True)
        return keywords_data
        
    except Exception as e:
        raise Exception(f"Error fetching from Google Search Console: {str(e)}")


def _generate_url_variations(url: str, properties_list: list = None) -> List[str]:
    """
    Generate different URL format variations for GSC property matching
    GSC properties can be registered as:
    1. Domain properties: sc-domain:example.com
    2. URL properties: https://example.com/
    
    Prioritizes exact matches from properties_list first!
    
    Args:
        url: The base URL
        properties_list: List of available properties to match against
        
    Returns:
        List of URL variations to try (prioritized by relevance)
    """
    from urllib.parse import urlparse
    
    # Ensure URL has a protocol
    if not url.startswith(('http://', 'https://')):
        base_url = f'https://{url}'
    else:
        base_url = url
    
    # Remove trailing slash and path for domain extraction
    base_url_clean = base_url.rstrip('/')
    parsed = urlparse(base_url_clean)
    domain = parsed.netloc
    path = parsed.path
    protocol = parsed.scheme
    
    # Extract base domain (without www)
    if domain.startswith('www.'):
        base_domain = domain[4:]
    else:
        base_domain = domain
    
    variations = []
    matched_properties = []
    
    # FIRST: If properties_list is provided, find exact or close matches
    if properties_list:
        for prop in properties_list:
            # Check if this property matches the user's input domain
            if _property_matches_domain(prop, base_domain, domain):
                matched_properties.append(prop)
        
        # Add matched properties first (highest priority)
        variations.extend(matched_properties)
    
    # SECOND: Add all other properties from the list (they might have path variations)
    if properties_list:
        for prop in properties_list:
            if prop not in variations:
                variations.append(prop)
    
    # THIRD: Add generated variations for the user's input
    generated = set()
    
    # Protocol + domain variations
    generated.add(f'{protocol}://{domain}')
    generated.add(f'{protocol}://{domain}/')
    generated.add(f'sc-domain:{base_domain}')
    generated.add(f'sc-domain:www.{base_domain}')
    
    # With and without www
    if domain.startswith('www.'):
        non_www = domain[4:]
        generated.add(f'{protocol}://{non_www}')
        generated.add(f'{protocol}://{non_www}/')
        generated.add(f'sc-domain:{non_www}')
    else:
        with_www = f'www.{domain}'
        generated.add(f'{protocol}://{with_www}')
        generated.add(f'{protocol}://{with_www}/')
        generated.add(f'sc-domain:www.{domain}')
    
    # With path if provided
    if path and path != '/':
        generated.add(f'{protocol}://{domain}{path}')
        generated.add(f'{protocol}://{domain}{path}/')
    
    variations.extend(list(generated))
    
    # Remove any duplicates while preserving order
    seen = set()
    unique_variations = []
    for v in variations:
        if v not in seen:
            unique_variations.append(v)
            seen.add(v)
    
    return unique_variations


def _property_matches_domain(property_str: str, base_domain: str, domain_with_www: str) -> bool:
    """
    Check if a GSC property matches the given domain
    
    Args:
        property_str: The GSC property (e.g., "sc-domain:example.com" or "https://example.com/")
        base_domain: The base domain without www (e.g., "example.com")
        domain_with_www: The domain as entered (e.g., "www.example.com" or "example.com")
        
    Returns:
        True if the property matches
    """
    property_lower = property_str.lower()
    base_domain_lower = base_domain.lower()
    domain_www_lower = domain_with_www.lower()
    
    # Domain property match
    if property_lower.startswith('sc-domain:'):
        prop_domain = property_lower.replace('sc-domain:', '').rstrip('/')
        # Match if exactly same, or one with www and one without
        return (prop_domain == base_domain_lower or 
                prop_domain == domain_www_lower or
                prop_domain == f'www.{base_domain_lower}')
    
    # URL property match
    elif property_lower.startswith('http'):
        from urllib.parse import urlparse
        try:
            prop_parsed = urlparse(property_lower)
            prop_domain = prop_parsed.netloc.lower()
            # Match if domain is the same
            return (prop_domain == domain_www_lower or 
                    prop_domain == base_domain_lower or
                    prop_domain == f'www.{base_domain_lower}')
        except:
            return False
    
    return False



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
