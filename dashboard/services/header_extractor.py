"""
Service to extract content headers (H1-H6) from web pages
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict


def extract_headers(url: str, timeout: int = 30) -> List[Dict[str, str]]:
    """
    Extract all heading tags (H1-H6) from a given URL
    
    Args:
        url: The URL to extract headers from
        timeout: Request timeout in seconds
        
    Returns:
        List of dictionaries containing header level and text
        Example: [
            {'level': 'H1', 'text': 'Main Title'},
            {'level': 'H2', 'text': 'Subtitle'},
            {'level': 'H3', 'text': 'Section Title'},
        ]
    """
    try:
        # Set a proper user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch the webpage
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract all heading tags
        extracted_headers = []
        heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        
        # Find all headings in order of appearance
        for element in soup.find_all(heading_tags):
            header_level = element.name.upper()
            header_text = element.get_text(strip=True)
            
            # Only add non-empty headers
            if header_text:
                extracted_headers.append({
                    'level': header_level,
                    'text': header_text
                })
        
        return extracted_headers
        
    except requests.exceptions.Timeout:
        raise Exception(f"Request timed out while fetching headers from {url}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching headers: {str(e)}")
    except Exception as e:
        raise Exception(f"Error parsing headers: {str(e)}")


def get_header_hierarchy(headers: List[Dict[str, str]]) -> Dict[str, int]:
    """
    Get statistics about header usage
    
    Args:
        headers: List of header dictionaries
        
    Returns:
        Dictionary with count of each header level
    """
    hierarchy = {
        'H1': 0,
        'H2': 0,
        'H3': 0,
        'H4': 0,
        'H5': 0,
        'H6': 0,
    }
    
    for header in headers:
        level = header.get('level', '')
        if level in hierarchy:
            hierarchy[level] += 1
    
    return hierarchy
