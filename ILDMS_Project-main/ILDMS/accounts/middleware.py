import re
import logging
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware:
    """Custom middleware to add additional security headers"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content Security Policy for forms and uploads
        if request.path.startswith('/documents/'):
            response['Content-Security-Policy'] = (
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
        
        return response


class RequestValidationMiddleware:
    """Middleware to validate and sanitize incoming requests"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Patterns for detecting potential attacks
        self.xss_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'vbscript:', re.IGNORECASE),
            re.compile(r'onload\s*=', re.IGNORECASE),
            re.compile(r'onerror\s*=', re.IGNORECASE),
        ]
        
        self.sql_injection_patterns = [
            re.compile(r'union\s+select', re.IGNORECASE),
            re.compile(r'drop\s+table', re.IGNORECASE),
            re.compile(r'delete\s+from', re.IGNORECASE),
            re.compile(r'insert\s+into', re.IGNORECASE),
            re.compile(r'update\s+\w+\s+set', re.IGNORECASE),
        ]
        
        self.path_traversal_patterns = [
            re.compile(r'\.\.\/'),
            re.compile(r'\.\.\\'),
            re.compile(r'%2e%2e%2f', re.IGNORECASE),
            re.compile(r'%2e%2e%5c', re.IGNORECASE),
        ]
    
    def __call__(self, request):
        # Skip validation for document uploads to prevent issues
        if any(path in request.path for path in ['/upload/', '/create/', '/documents/']):
            logger.info(f"Skipping request validation for {request.path}")
            response = self.get_response(request)
            return response
            
        # Validate request data
        try:
            self._validate_request_data(request)
        except PermissionDenied as e:
            logger.warning(f"Request validation failed for {request.path}: {e}")
            raise
        
        response = self.get_response(request)
        return response
    
    def _validate_request_data(self, request):
        """Validate GET and POST data for potential attacks"""
        
        # Skip all validation for document upload/create paths
        if any(path in request.path for path in ['/upload/', '/create/', '/documents/']):
            return
        
        # Skip validation for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return
            
        # Skip validation for file uploads (multipart/form-data)
        content_type = getattr(request, 'content_type', '') or request.META.get('CONTENT_TYPE', '')
        if 'multipart/form-data' in content_type:
            return
        
        # Check GET parameters
        for key, value in request.GET.items():
            if isinstance(value, str):
                self._check_for_attacks(value, f"GET parameter '{key}'")
        
        # Check POST parameters for other requests
        if request.method == 'POST':
            for key, value in request.POST.items():
                if isinstance(value, str):
                    self._check_for_attacks(value, f"POST parameter '{key}'")
        
        # Check path for traversal attempts (but be more lenient)
        for pattern in self.path_traversal_patterns:
            if pattern.search(request.path):
                # Only block obvious traversal attempts, not legitimate paths
                if '../' in request.path or '..\\' in request.path:
                    logger.warning(f"Path traversal attempt detected: {request.path} from {request.META.get('REMOTE_ADDR')}")
                    raise PermissionDenied("Invalid request path")
    
    def _check_for_attacks(self, value, context):
        """Check individual values for attack patterns"""
        
        # Skip CKEditor content (it needs HTML)
        if context.startswith('POST parameter') and any(x in context.lower() for x in ['content', 'html_content']):
            return
        
        # Check for XSS attempts
        for pattern in self.xss_patterns:
            if pattern.search(value):
                logger.warning(f"Potential XSS attempt in {context}: {value[:100]}")
                raise PermissionDenied("Invalid request content")
        
        # Check for SQL injection attempts
        for pattern in self.sql_injection_patterns:
            if pattern.search(value):
                logger.warning(f"Potential SQL injection attempt in {context}: {value[:100]}")
                raise PermissionDenied("Invalid request content")


class SessionSecurityMiddleware:
    """Enhanced session security middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip session validation for uploads to prevent issues
        if any(path in request.path for path in ['/upload/', '/create/', '/documents/']):
            response = self.get_response(request)
            return response
            
        # Check for session hijacking attempts
        if request.user.is_authenticated:
            self._validate_session(request)
        
        response = self.get_response(request)
        
        # Update session security info
        if request.user.is_authenticated:
            self._update_session_security(request)
        
        return response
    
    def _validate_session(self, request):
        """Validate session for potential hijacking"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        remote_addr = request.META.get('REMOTE_ADDR', '')
        
        # Check if session has security markers
        session_user_agent = request.session.get('security_user_agent')
        session_remote_addr = request.session.get('security_remote_addr')
        
        if session_user_agent and session_user_agent != user_agent:
            logger.warning(f"Session user agent mismatch for user {request.user.username}")
            logout(request)
            raise PermissionDenied("Session security violation")
        
        # Allow IP changes but log them (for mobile users, etc.)
        if session_remote_addr and session_remote_addr != remote_addr:
            logger.info(f"IP address change for user {request.user.username}: {session_remote_addr} -> {remote_addr}")
    
    def _update_session_security(self, request):
        """Update session with security information"""
        request.session['security_user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        request.session['security_remote_addr'] = request.META.get('REMOTE_ADDR', '')
        request.session['security_last_activity'] = request.session.get_session_cookie_age()
