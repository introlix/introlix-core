import re
from contextlib import contextmanager

import lxml.html
import lxml.sax
from bs4 import BeautifulSoup

unicode = str

DEFAULT_ENCODING = 'utf8'
DEFAULT_ENC_ERRORS = 'replace'
CHARSET_META_TAG_PATTERN = re.compile(br"""<meta[^>]+charset=["']?([^'"/>\s]+)""", re.IGNORECASE)

class JustextError(Exception):
    "Base class for jusText exceptions."

@contextmanager
def ignored(*exceptions):
    try:
        yield
    except tuple(exceptions):
        pass

def html_to_dom(html, default_encoding=DEFAULT_ENCODING, encoding=None, errors=DEFAULT_ENC_ERRORS):
    """Converts HTML to DOM."""
    if isinstance(html, unicode):
        decoded_html = html
        # encode HTML for case it's XML with encoding declaration
        forced_encoding = encoding if encoding else default_encoding
        html = html.encode(forced_encoding, errors)
    else:
        decoded_html = decode_html(html, default_encoding, encoding, errors)

    try:
        dom = lxml.html.fromstring(decoded_html, parser=lxml.html.HTMLParser())
    except ValueError:
        # Unicode strings with encoding declaration are not supported.
        # for XHTML files with encoding declaration, use the declared encoding
        dom = lxml.html.fromstring(html, parser=lxml.html.HTMLParser())

    return dom


def decode_html(html, default_encoding=DEFAULT_ENCODING, encoding=None, errors=DEFAULT_ENC_ERRORS):
    """
    Converts a `html` containing an HTML page into Unicode.
    Tries to guess character encoding from meta tag.
    """
    if isinstance(html, unicode):
        return html

    if encoding:
        return html.decode(encoding, errors)

    match = CHARSET_META_TAG_PATTERN.search(html)
    if match:
        declared_encoding = match.group(1).decode("ASCII")
        # proceed unknown encoding as if it wasn't found at all
        with ignored(LookupError):
            return html.decode(declared_encoding, errors)

    # unknown encoding
    try:
        # try UTF-8 first
        return html.decode("utf8")
    except UnicodeDecodeError:
        # try lucky with default encoding
        try:
            return html.decode(default_encoding, errors)
        except UnicodeDecodeError as e:
            raise JustextError("Unable to decode the HTML to Unicode: " + unicode(e))

# def html_to_dom(html, encoding=None):
#     """Converts HTML to DOM using BeautifulSoup."""
#     # Attempt to decode HTML
#     decoded_html = decode_html(html, encoding)
    
#     # Create a BeautifulSoup object and return it as the DOM
#     soup = BeautifulSoup(decoded_html, 'lxml')
#     return soup

# def decode_html(html, encoding=None):
#     """
#     Converts a `html` containing an HTML page into Unicode.
#     Tries to guess character encoding from meta tag.
#     """
#     if isinstance(html, bytes):
#         html = html.decode(encoding or DEFAULT_ENCODING, DEFAULT_ENC_ERRORS)
        
#     if isinstance(html, str):
#         # Check for charset in meta tag
#         match = CHARSET_META_TAG_PATTERN.search(html)
#         if match:
#             declared_encoding = match.group(1)
#             html = html.encode('utf-8').decode(declared_encoding, DEFAULT_ENC_ERRORS)

#     return html