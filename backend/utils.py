"""
Utility functions for CardosoX Scraper
"""

from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
import re


def validate_urls(urls: List[str]) -> Dict[str, Any]:
    """
    Validate list of URLs
    
    Returns:
        {
            'valid': bool,
            'message': str,
            'valid_urls': List[str]
        }
    """
    if not urls:
        return {
            'valid': False,
            'message': 'No URLs provided'
        }
    
    if not isinstance(urls, list):
        return {
            'valid': False,
            'message': 'URLs must be a list'
        }
    
    if len(urls) > 10:
        return {
            'valid': False,
            'message': 'Maximum 10 URLs allowed per request'
        }
    
    valid_urls = []
    invalid_urls = []
    
    for url in urls:
        url = url.strip() if isinstance(url, str) else url
        
        if not url:
            continue
        
        if is_valid_url(url):
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            valid_urls.append(url)
        else:
            invalid_urls.append(url)
    
    if not valid_urls:
        return {
            'valid': False,
            'message': 'No valid URLs found'
        }
    
    result = {
        'valid': True,
        'message': 'All URLs are valid',
        'valid_urls': valid_urls,
        'count': len(valid_urls)
    }
    
    if invalid_urls:
        result['message'] = f'Validated {len(valid_urls)} URLs. {len(invalid_urls)} invalid.'
        result['invalid_urls'] = invalid_urls
    
    return result


def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL"""
    if not isinstance(url, str) or not url:
        return False
    
    url = url.strip()
    
    # Basic URL pattern
    url_pattern = r'^(https?://)?([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}.*$'
    
    if not re.match(url_pattern, url, re.IGNORECASE):
        return False
    
    # Additional check with urlparse
    try:
        result = urlparse(url if url.startswith(('http://', 'https://')) else 'https://' + url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def format_response(
    status: str,
    results: List[Dict[str, Any]] = None,
    message: str = None
) -> Dict[str, Any]:
    """Format API response"""
    response = {
        'status': status,
    }
    
    if results:
        response['results'] = results
        response['count'] = len(results)
    
    if message:
        response['message'] = message
    
    return response


def sanitize_email(email: str) -> str:
    """Sanitize and validate email"""
    if not email:
        return None
    
    email = email.strip().lower()
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(email_pattern, email):
        return email
    
    return None


def sanitize_phone(phone: str) -> str:
    """Sanitize phone number (remove special chars but keep structure)"""
    if not phone:
        return None
    
    # Keep only digits and common separators
    phone = ''.join(c for c in phone if c.isdigit() or c in '+-() ')
    phone = phone.strip()
    
    # Basic validation - at least 7 digits
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) >= 7:
        return phone
    
    return None


def sanitize_address(address: str) -> str:
    """Sanitize address"""
    if not address:
        return None
    
    address = address.strip()
    
    # Remove extra whitespace
    address = ' '.join(address.split())
    
    # Minimum length
    if len(address) >= 5:
        return address
    
    return None


def create_csv_row(data: Dict[str, Any]) -> str:
    """Create CSV row from data dict"""
    def escape_csv(val):
        if val is None:
            return ''
        val = str(val)
        if ',' in val or '"' in val or '\n' in val:
            val = '"' + val.replace('"', '""') + '"'
        return val
    
    return ','.join([
        escape_csv(data.get('url')),
        escape_csv(data.get('company_name')),
        escape_csv('; '.join(data.get('emails', []))),
        escape_csv('; '.join(data.get('phone_numbers', []))),
        escape_csv('; '.join(data.get('addresses', []))),
        escape_csv(data.get('status'))
    ])


def create_csv_header() -> str:
    """Create CSV header"""
    return 'URL,Company Name,Emails,Phone Numbers,Addresses,Status'
