import re
from urllib.parse import urlparse, quote

def is_valid_url(url):
    """
    Validate the URL format.
    """
    try:
        parsed_url = urlparse(url)
        return all([parsed_url.scheme, parsed_url.netloc])
    except Exception:
        return False

def sanitize_url(url):
    """
    Sanitizes the URL by encoding non-ASCII characters while leaving URL-safe characters intact.
    """
    sanitized_url = url.strip()  # Remove extra spaces
    return quote(sanitized_url, safe=":/?#[]@!$&'()*+,;=")  # Encode only non-ASCII characters