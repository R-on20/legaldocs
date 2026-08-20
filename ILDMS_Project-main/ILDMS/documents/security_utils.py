"""
Security utility functions for the ILDMS project.
Provides common security operations like input sanitization, 
file validation, and content filtering.
"""

import re
import logging
from django.utils.html import escape, strip_tags
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import bleach

logger = logging.getLogger(__name__)

# HTML sanitization settings
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'a', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
    'span', 'div'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'table': ['border', 'cellpadding', 'cellspacing'],
    'span': ['style'],
    'div': ['style'],
}

ALLOWED_STYLES = ['font-weight', 'font-style', 'text-decoration', 'color', 'background-color']

# Dangerous patterns to detect
XSS_PATTERNS = [
    re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'vbscript:', re.IGNORECASE),
    re.compile(r'onload\s*=', re.IGNORECASE),
    re.compile(r'onerror\s*=', re.IGNORECASE),
    re.compile(r'onclick\s*=', re.IGNORECASE),
    re.compile(r'onmouseover\s*=', re.IGNORECASE),
]

SQL_INJECTION_PATTERNS = [
    re.compile(r'union\s+select', re.IGNORECASE),
    re.compile(r'drop\s+table', re.IGNORECASE),
    re.compile(r'delete\s+from', re.IGNORECASE),
    re.compile(r'insert\s+into', re.IGNORECASE),
    re.compile(r'update\s+\w+\s+set', re.IGNORECASE),
    re.compile(r'exec\s*\(', re.IGNORECASE),
]


def sanitize_html_content(content, allowed_tags=None, allowed_attributes=None):
    """
    Sanitize HTML content using bleach library.
    Removes dangerous tags and attributes while preserving safe formatting.
    """
    if not content:
        return content
    
    try:
        cleaned_content = bleach.clean(
            content,
            tags=allowed_tags or ALLOWED_TAGS,
            attributes=allowed_attributes or ALLOWED_ATTRIBUTES,
            styles=ALLOWED_STYLES,
            strip=True
        )
        return cleaned_content
    except Exception as e:
        logger.error(f"HTML sanitization error: {e}")
        # Fallback to strip all HTML
        return strip_tags(content)


def sanitize_user_input(input_text, max_length=None, allow_html=False):
    """
    Sanitize general user input.
    """
    if not input_text:
        return input_text
    
    # Convert to string if not already
    input_text = str(input_text)
    
    if not allow_html:
        # Remove all HTML tags
        input_text = strip_tags(input_text)
        
        # Escape remaining HTML entities
        input_text = escape(input_text)
    else:
        # Sanitize HTML content
        input_text = sanitize_html_content(input_text)
    
    # Check for dangerous patterns
    if contains_dangerous_patterns(input_text):
        logger.warning(f"Dangerous patterns detected in input: {input_text[:100]}...")
        raise ValidationError(_("Input contains potentially dangerous content."))
    
    # Trim to max length if specified
    if max_length and len(input_text) > max_length:
        input_text = input_text[:max_length]
    
    return input_text.strip()


def contains_dangerous_patterns(text):
    """
    Check if text contains potentially dangerous patterns.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for XSS patterns
    for pattern in XSS_PATTERNS:
        if pattern.search(text_lower):
            return True
    
    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(text_lower):
            return True
    
    return False


def validate_search_query(query, max_length=200):
    """
    Validate and sanitize search queries.
    """
    if not query:
        return query
    
    # Remove potentially dangerous characters
    cleaned_query = re.sub(r'[<>"\';]', '', query)
    
    # Check length
    if len(cleaned_query) > max_length:
        raise ValidationError(f"Search query too long. Maximum {max_length} characters.")
    
    # Check for dangerous patterns
    if contains_dangerous_patterns(cleaned_query):
        raise ValidationError(_("Search query contains invalid characters."))
    
    return cleaned_query.strip()


def sanitize_filename(filename):
    """
    Sanitize filename for secure storage.
    """
    if not filename:
        return 'unnamed_file'
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[\x00-\x1f]', '', filename)  # Remove control characters
    filename = filename.strip('. ')  # Remove leading/trailing dots and spaces
    
    # Ensure filename is not empty after sanitization
    if not filename:
        filename = 'unnamed_file'
    
    return filename


def validate_file_content_type(file, expected_type):
    """
    Validate file content matches expected type using magic bytes.
    """
    try:
        import magic
        
        # Read first 2KB for magic detection
        file.seek(0)
        file_header = file.read(2048)
        file.seek(0)
        
        detected_type = magic.from_buffer(file_header, mime=True)
        
        if not detected_type.startswith(expected_type):
            raise ValidationError(
                f"File content type {detected_type} does not match expected type {expected_type}"
            )
            
    except ImportError:
        logger.warning("python-magic not available, skipping content type validation")
    except Exception as e:
        logger.error(f"Content type validation error: {e}")


def log_security_event(event_type, user, details, request=None):
    """
    Log security-related events for monitoring.
    """
    log_data = {
        'event_type': event_type,
        'user': str(user) if user else 'Anonymous',
        'details': details,
    }
    
    if request:
        log_data.update({
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'path': request.path,
        })
    
    logger.warning(f"Security Event [{event_type}]: {log_data}")


class SecurityMixin:
    """
    Mixin to add security validation to Django forms and models.
    """
    
    def clean_text_field(self, field_name, max_length=None, allow_html=False):
        """
        Generic method to clean text fields with security validation.
        """
        value = self.cleaned_data.get(field_name)
        if value:
            return sanitize_user_input(value, max_length, allow_html)
        return value
    
    def validate_no_scripts(self, text):
        """
        Validate that text doesn't contain script tags or dangerous content.
        """
        if text and contains_dangerous_patterns(text):
            raise ValidationError(_("Content contains potentially dangerous elements."))


# Content Security Policy helpers
def get_csp_header_for_ckeditor():
    """
    Get Content Security Policy header that allows CKEditor to function.
    """
    return (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "media-src 'self'; "
        "object-src 'none'; "
        "frame-src 'none';"
    )


def get_restrictive_csp_header():
    """
    Get a restrictive CSP header for pages that don't need rich content.
    """
    return (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self'; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "frame-src 'none';"
    )


# File upload security
DANGEROUS_EXTENSIONS = [
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
    '.app', '.deb', '.pkg', '.dmg', '.zip', '.rar', '.7z', '.tar', '.gz',
    '.ps1', '.sh', '.php', '.asp', '.jsp'
]


def is_safe_file_extension(filename):
    """
    Check if file extension is safe for upload.
    """
    if not filename:
        return False
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    return f'.{ext}' not in DANGEROUS_EXTENSIONS


def validate_uploaded_file(uploaded_file):
    """
    Comprehensive validation for uploaded files.
    """
    # Check filename safety
    if not is_safe_file_extension(uploaded_file.name):
        raise ValidationError(_("File type not allowed for security reasons."))
    
    # Check file size (500MB absolute limit)
    if uploaded_file.size > 500 * 1024 * 1024:
        raise ValidationError(_("File size exceeds maximum limit of 500MB."))
    
    # Check for null bytes in filename
    if '\x00' in uploaded_file.name:
        raise ValidationError(_("Invalid filename."))
    
    # Sanitize filename
    uploaded_file.name = sanitize_filename(uploaded_file.name)


# Export commonly used functions
__all__ = [
    'sanitize_html_content',
    'sanitize_user_input', 
    'contains_dangerous_patterns',
    'validate_search_query',
    'sanitize_filename',
    'validate_file_content_type',
    'log_security_event',
    'SecurityMixin',
    'get_csp_header_for_ckeditor',
    'get_restrictive_csp_header',
    'is_safe_file_extension',
    'validate_uploaded_file',
]
