"""
Service to extract images and their alt text from web pages
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urljoin, urlparse


def extract_images(url: str, timeout: int = 30) -> List[Dict[str, str]]:
    """
    Extract all images and their alt text from a given URL
    
    Args:
        url: The URL to extract images from
        timeout: Request timeout in seconds
        
    Returns:
        List of dictionaries containing image source and alt text
        Example: [
            {'src': 'https://example.com/image1.jpg', 'alt': 'Description', 'status': 'OK'},
            {'src': 'https://example.com/image2.png', 'alt': '', 'status': 'Missing'},
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
        
        # Extract all image tags
        extracted_images = []
        
        # Find all img tags
        for img in soup.find_all('img'):
            # Get the image source
            img_src = img.get('src', '')
            
            # Convert relative URLs to absolute URLs
            if img_src:
                img_src = urljoin(url, img_src)
            
            # Get the alt attribute
            img_alt = img.get('alt', '')
            
            # Determine status
            if img_alt:
                status = 'OK'
            elif img_alt == '':  # Empty string means decorative or missing
                status = 'Missing'
            else:
                status = 'Missing'
            
            extracted_images.append({
                'src': img_src,
                'alt': img_alt,
                'status': status
            })
        
        return extracted_images
        
    except requests.RequestException as e:
        raise Exception(f"Error fetching URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error extracting images: {str(e)}")


def get_image_stats(images: List[Dict[str, str]]) -> Dict[str, int]:
    """
    Get statistics about the images
    
    Args:
        images: List of image dictionaries
        
    Returns:
        Dictionary with image statistics
    """
    total_images = len(images)
    images_with_alt = sum(1 for img in images if img['status'] == 'OK')
    images_without_alt = sum(1 for img in images if img['status'] == 'Missing')
    
    return {
        'total_images': total_images,
        'images_with_alt': images_with_alt,
        'images_without_alt': images_without_alt,
    }
