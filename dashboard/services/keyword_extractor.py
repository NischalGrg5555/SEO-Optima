"""
Service to extract keywords and ranking data from Google Search Console
"""
import importlib
import random
from typing import List, Dict, Optional
from urllib.parse import urlparse
from datetime import datetime, timedelta


class GSCAuthError(Exception):
    """Raised when stored Google credentials are invalid or revoked."""


def _load_google_clients():
    try:
        googleapiclient_discovery = importlib.import_module('googleapiclient.discovery')
        google_oauth2_credentials = importlib.import_module('google.oauth2.credentials')
        google_transport_requests = importlib.import_module('google.auth.transport.requests')
        google_auth_exceptions = importlib.import_module('google.auth.exceptions')
    except ImportError as exc:
        raise Exception(
            'Google Search Console dependencies are not installed. '
            'Install packages from requirements.txt to use this feature.'
        ) from exc

    return (
        googleapiclient_discovery.build,
        google_oauth2_credentials.Credentials,
        google_transport_requests.Request,
        google_auth_exceptions.RefreshError,
    )


def _is_auth_error(error_text: str) -> bool:
    """Detect OAuth auth/refresh failures from API/client exceptions."""
    if not error_text:
        return False
    text = error_text.lower()
    indicators = [
        'invalid_grant',
        'expired or revoked',
        'token has been expired or revoked',
        'invalid credentials',
        'unauthorized',
        'insufficient authentication',
    ]
    return any(token in text for token in indicators)


def _to_display_url(value: str) -> str:
    """Convert GSC property value to a clickable URL for UI fallback values."""
    if value and value.startswith('sc-domain:'):
        return f"https://{value.replace('sc-domain:', '').strip('/')}"
    return value


def fetch_gsc_keywords(url: str, credentials_dict: dict, properties_list: list = None, days: int = 7) -> List[Dict[str, any]]:
    """
    Fetch real keyword data from Google Search Console API
    
    Args:
        url: The URL/property to fetch keywords for
        credentials_dict: OAuth2 credentials as dictionary
        properties_list: List of available properties from GSC (for smart matching)
        days: Number of days of data to fetch (default: 7)
        
    Returns:
        List of dictionaries containing keyword data
    """
    try:
        build, Credentials, Request, RefreshError = _load_google_clients()

        # Create credentials object from dictionary
        credentials = Credentials(
            token=credentials_dict.get('token'),
            refresh_token=credentials_dict.get('refresh_token'),
            token_uri=credentials_dict.get('token_uri'),
            client_id=credentials_dict.get('client_id'),
            client_secret=credentials_dict.get('client_secret'),
            scopes=credentials_dict.get('scopes', ['https://www.googleapis.com/auth/webmasters.readonly'])
        )

        # Refresh proactively so auth failures surface clearly to callers.
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except RefreshError as e:
                raise GSCAuthError(
                    "Google Search Console connection expired or revoked. "
                    "Please reconnect your Google account."
                ) from e

        if not credentials.valid and not credentials.refresh_token:
            raise GSCAuthError(
                "Google Search Console credentials are incomplete. "
                "Please reconnect your Google account."
            )
        
        # Build the Search Console service
        service = build('searchconsole', 'v1', credentials=credentials)
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Prepare the base request for paginated fetching.
        # We request query+page so each keyword row contains the exact ranked URL.
        page_size = 500
        max_total_rows = 10000
        base_request = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'dimensions': ['query', 'page'],
            'type': 'web',
            'rowLimit': page_size,
        }
        
        # Generate different URL format variations to try, including domain properties
        url_variations = _generate_url_variations(url, properties_list)
        
        keywords_data = []
        last_error = None
        
        # Try each URL variation
        for site_url in url_variations:
            try:
                start_row = 0
                fetched_any_rows = False

                keyword_aggregates = {}

                while start_row < max_total_rows:
                    request_body = {
                        **base_request,
                        'startRow': start_row,
                    }

                    response = service.searchanalytics().query(
                        siteUrl=site_url,
                        body=request_body
                    ).execute()

                    rows = response.get('rows', [])
                    if not rows:
                        break

                    fetched_any_rows = True

                    for row in rows:
                        keys = row.get('keys', [])
                        if len(keys) < 2:
                            # Skip malformed rows rather than injecting a fallback URL,
                            # to keep keyword->page mapping accurate.
                            continue

                        keyword = keys[0]  # query
                        ranked_url = keys[1]  # page

                        # Get metrics
                        clicks = int(row.get('clicks', 0))
                        impressions = int(row.get('impressions', 0))
                        position = float(row.get('position', 0))

                        agg = keyword_aggregates.setdefault(
                            keyword,
                            {
                                'keyword': keyword,
                                'clicks': 0,
                                'volume': 0,
                                'weighted_position_sum': 0.0,
                                'url': ranked_url,
                                'best_url_impressions': -1,
                            }
                        )

                        agg['clicks'] += clicks
                        agg['volume'] += impressions
                        agg['weighted_position_sum'] += (position * impressions)

                        # Keep the URL from the strongest page impression for this keyword.
                        if impressions > agg['best_url_impressions']:
                            agg['url'] = ranked_url
                            agg['best_url_impressions'] = impressions

                    # If fewer than page_size rows returned, this is the last page
                    if len(rows) < page_size:
                        break

                    start_row += page_size

                if fetched_any_rows and keyword_aggregates:
                    keywords_data = []
                    for agg in keyword_aggregates.values():
                        impressions = agg['volume']
                        clicks = agg['clicks']
                        ctr_percentage = (clicks / impressions * 100) if impressions else 0
                        avg_position = (agg['weighted_position_sum'] / impressions) if impressions else 0

                        keywords_data.append({
                            'keyword': agg['keyword'],
                            'volume': impressions,
                            'position': round(avg_position, 1),
                            'url': agg['url'],
                            'clicks': clicks,
                            'ctr': round(ctr_percentage, 2),
                        })

                    keywords_data.sort(key=lambda x: x['volume'], reverse=True)
                    return keywords_data
                    
            except Exception as e:
                if _is_auth_error(str(e)):
                    raise GSCAuthError(
                        "Google Search Console connection expired or revoked. "
                        "Please reconnect your Google account."
                    ) from e
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
        
    except GSCAuthError:
        raise
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
    
    input_url = (url or '').strip()

    # Handle direct domain property selection from GSC
    if input_url.startswith('sc-domain:'):
        domain = input_url.replace('sc-domain:', '').rstrip('/')
        base_domain = domain[4:] if domain.startswith('www.') else domain
        protocol = 'https'
        path = ''
        variations = [input_url]
    else:
        # Ensure URL has a protocol
        if not input_url.startswith(('http://', 'https://')):
            base_url = f'https://{input_url}'
        else:
            base_url = input_url

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
