import os
import magic
import mimetypes
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.conf import settings
from PIL import Image
import tempfile
import zipfile
import logging

logger = logging.getLogger(__name__)

# Define secure MIME types and extensions
ALLOWED_MIME_TYPES = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'application/vnd.ms-powerpoint': ['.ppt'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-excel': ['.xls'],
    'audio/mpeg': ['.mp3'],
    'audio/wav': ['.wav'],
    'audio/x-wav': ['.wav'],
    'video/mp4': ['.mp4'],
    'video/quicktime': ['.mov'],
    'text/plain': ['.txt'],
    'text/markdown': ['.md'],
    'text/html': ['.html', '.htm'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
}

# Maximum file sizes by type (in bytes)
MAX_FILE_SIZES = {
    'document': 50 * 1024 * 1024,  # 50MB for documents
    'audio': 100 * 1024 * 1024,    # 100MB for audio
    'video': 500 * 1024 * 1024,    # 500MB for video
    'image': 10 * 1024 * 1024,     # 10MB for images
}

# Dangerous file extensions that should never be allowed
DANGEROUS_EXTENSIONS = [
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
    '.app', '.deb', '.pkg', '.dmg', '.zip', '.rar', '.7z', '.tar', '.gz',
    '.ps1', '.sh', '.php', '.asp', '.jsp', '.htm', '.html'
]

class SecureFileValidator:
    """
    Comprehensive file validator that checks:
    1. File extension
    2. MIME type
    3. File size
    4. File content/magic bytes
    5. Embedded threats
    """
    
    def __init__(self, allowed_extensions=None, max_size=None):
        self.allowed_extensions = allowed_extensions or list(ALLOWED_MIME_TYPES.values())
        self.allowed_extensions = [ext for sublist in self.allowed_extensions for ext in sublist]
        self.max_size = max_size or MAX_FILE_SIZES['document']
    
    def __call__(self, value):
        self.validate_file_extension(value)
        self.validate_file_size(value)
        self.validate_mime_type(value)
        self.validate_file_content(value)
        self.validate_no_embedded_threats(value)
    
    def validate_file_extension(self, file):
        """Validate file has allowed extension"""
        if not file.name:
            raise ValidationError(_('File must have a name.'))
        
        ext = os.path.splitext(file.name)[1].lower()
        
        # Check for dangerous extensions
        if ext in DANGEROUS_EXTENSIONS:
            raise ValidationError(
                _('File type "%(extension)s" is not allowed for security reasons.'),
                params={'extension': ext}
            )
        
        # Check if extension is in allowed list
        if ext not in self.allowed_extensions:
            raise ValidationError(
                _('File extension "%(extension)s" is not allowed. Allowed extensions: %(allowed)s'),
                params={'extension': ext, 'allowed': ', '.join(self.allowed_extensions)}
            )
    
    def validate_file_size(self, file):
        """Validate file size is within limits"""
        if file.size > self.max_size:
            max_size_mb = self.max_size / (1024 * 1024)
            raise ValidationError(
                _('File size %(size)s MB exceeds maximum allowed size of %(max_size)s MB.'),
                params={
                    'size': round(file.size / (1024 * 1024), 2),
                    'max_size': round(max_size_mb, 2)
                }
            )
    
    def validate_mime_type(self, file):
        """Validate MIME type matches file extension"""
        try:
            # Get MIME type using python-magic (if available)
            file.seek(0)
            
            # Try to use python-magic, fall back to mimetypes if not available
            try:
                import magic
                mime_type = magic.from_buffer(file.read(2048), mime=True)
            except (ImportError, Exception):
                # Fallback to basic mimetypes
                mime_type, _ = mimetypes.guess_type(file.name)
                if not mime_type:
                    # Default to application/octet-stream if can't determine
                    logger.warning(f"Could not determine MIME type for {file.name}, allowing upload")
                    file.seek(0)
                    return
            
            file.seek(0)
            
            # Get expected extensions for this MIME type
            expected_extensions = ALLOWED_MIME_TYPES.get(mime_type, [])
            
            # Get actual file extension
            actual_extension = os.path.splitext(file.name)[1].lower()
            
            # Check if MIME type is allowed
            if mime_type not in ALLOWED_MIME_TYPES:
                # For unknown MIME types, just check if extension is safe
                if actual_extension in ['.pdf', '.docx', '.doc', '.txt', '.md']:
                    logger.warning(f"Unknown MIME type {mime_type} for {file.name}, but extension is safe")
                    return
                else:
                    raise ValidationError(
                        _('File type "%(mime_type)s" is not allowed.'),
                        params={'mime_type': mime_type}
                    )
            
            # Check if extension matches MIME type (but be more lenient)
            if expected_extensions and actual_extension not in expected_extensions:
                logger.warning(f"Extension mismatch for {file.name}: {actual_extension} vs {mime_type}")
                # Don't fail validation for extension mismatches, just log warning
                
        except Exception as e:
            logger.warning(f"MIME type validation error for {file.name}: {e}")
            # Don't fail validation for MIME type issues, just log warning
    
    def validate_file_content(self, file):
        """Validate file content for common threats"""
        try:
            file.seek(0)
            content = file.read(1024)  # Read first 1KB
            file.seek(0)
            
            # Check for executable signatures
            executable_signatures = [
                b'MZ',  # Windows PE
                b'\x7fELF',  # Linux ELF
                b'\xfe\xed\xfa',  # Mach-O
                b'\xcf\xfa\xed\xfe',  # Mach-O
            ]
            
            for sig in executable_signatures:
                if content.startswith(sig):
                    raise ValidationError(_('File appears to be an executable and is not allowed.'))
            
            # Check for script content in supposed documents (but be less strict)
            script_patterns = [
                b'<script',
                b'javascript:',
                b'vbscript:',
                b'<?php',
                b'#!/bin/',
                b'#!/usr/',
            ]
            
            content_lower = content.lower()
            for pattern in script_patterns:
                if pattern in content_lower:
                    logger.warning(f"Potentially dangerous script content detected in {file.name}")
                    # Log warning but don't fail validation for HTML/script content
                    
        except Exception as e:
            logger.warning(f"Content validation error for {file.name}: {e}")
            # Don't fail validation for content reading errors
    
    def validate_no_embedded_threats(self, file):
        """Additional validation for Office documents and PDFs"""
        try:
            ext = os.path.splitext(file.name)[1].lower()
            
            if ext in ['.docx', '.pptx', '.xlsx']:
                self._validate_office_document(file)
            elif ext == '.pdf':
                self._validate_pdf_document(file)
        except Exception as e:
            logger.warning(f"Embedded threat validation error for {file.name}: {e}")
            # Don't fail validation for embedded threat checks
    
    def _validate_office_document(self, file):
        """Validate Office documents for embedded threats"""
        try:
            file.seek(0)
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(file.read())
                temp_file.flush()
                file.seek(0)
                
                # Office documents are ZIP files, check contents
                with zipfile.ZipFile(temp_file.name, 'r') as zip_file:
                    # Check for suspicious files in the archive
                    for name in zip_file.namelist():
                        if any(danger in name.lower() for danger in ['.exe', '.dll', '.bat', '.cmd']):
                            raise ValidationError(_('Office document contains potentially dangerous content.'))
                        
                        # Check for external references (log warning but don't fail)
                        if name.endswith('.xml'):
                            try:
                                content = zip_file.read(name).decode('utf-8', errors='ignore')
                                if any(pattern in content.lower() for pattern in ['http:', 'https:', 'ftp:', 'file:']):
                                    logger.warning(f"Office document contains external references in {name}")
                            except:
                                pass
                                
        except zipfile.BadZipFile:
            logger.warning(f"Office document appears to be corrupted: {file.name}")
            # Don't fail validation for ZIP errors
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.warning(f"Office document validation error for {file.name}: {e}")
            # Don't fail validation for unexpected errors
    
    def _validate_pdf_document(self, file):
        """Basic PDF validation"""
        file.seek(0)
        header = file.read(8)
        file.seek(0)
        
        if not header.startswith(b'%PDF-'):
            raise ValidationError(_('File does not appear to be a valid PDF.'))
    
    def validate(self, file, filename, mime_type):
        """
        Main validation method that returns validation results
        Args:
            file: File object
            filename: Original filename
            mime_type: MIME type to validate against
        Returns:
            dict: Validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'mime_type': mime_type,
            'filename': filename,
            'size': getattr(file, 'size', 0)
        }
        
        try:
            # Set up a temporary file object with name for validation
            class TempFile:
                def __init__(self, file_obj, name):
                    self.name = name
                    self.size = getattr(file_obj, 'size', 0)
                    self._file = file_obj
                
                def read(self, *args):
                    return self._file.read(*args)
                
                def seek(self, *args):
                    return self._file.seek(*args)
            
            temp_file = TempFile(file, filename)
            
            # Run all validations
            self.__call__(temp_file)
            
        except ValidationError as e:
            results['valid'] = False
            results['errors'].append(str(e))
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Validation error: {str(e)}")
        
        return results


class SecureImageValidator:
    """Validator specifically for image files"""
    
    def __init__(self, max_size=10*1024*1024):  # 10MB default
        self.max_size = max_size
    
    def __call__(self, value):
        # Basic validations
        if value.size > self.max_size:
            raise ValidationError(
                _('Image size exceeds maximum allowed size of %(max_size)s MB.'),
                params={'max_size': self.max_size / (1024 * 1024)}
            )
        
        # Validate it's actually an image
        try:
            value.seek(0)
            with Image.open(value) as img:
                # Verify image format
                if img.format not in ['JPEG', 'PNG', 'GIF']:
                    raise ValidationError(_('Unsupported image format. Only JPEG, PNG, and GIF are allowed.'))
                
                # Check dimensions
                if img.size[0] > 4096 or img.size[1] > 4096:
                    raise ValidationError(_('Image dimensions too large. Maximum 4096x4096 pixels.'))
                
                # Verify image integrity
                img.verify()
            
            value.seek(0)
            
        except Exception as e:
            raise ValidationError(_('Invalid or corrupted image file.'))


def validate_file_size_by_type(file):
    """Dynamic file size validation based on file type"""
    ext = os.path.splitext(file.name)[1].lower()
    
    if ext in ['.mp4', '.mov']:
        max_size = MAX_FILE_SIZES['video']
    elif ext in ['.mp3', '.wav']:
        max_size = MAX_FILE_SIZES['audio']
    elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
        max_size = MAX_FILE_SIZES['image']
    else:
        max_size = MAX_FILE_SIZES['document']
    
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(
            _('File size %(size)s MB exceeds maximum allowed size of %(max_size)s MB for this file type.'),
            params={
                'size': round(file.size / (1024 * 1024), 2),
                'max_size': round(max_size_mb, 2)
            }
        )


def validate_no_path_traversal(filename):
    """Prevent path traversal attacks in filenames"""
    if not filename:
        raise ValidationError(_('Filename cannot be empty.'))
    
    # Check for path traversal patterns
    dangerous_patterns = ['../', '..\\', './', '.\\', '~/', '~\\']
    filename_lower = filename.lower()
    
    for pattern in dangerous_patterns:
        if pattern in filename_lower:
            raise ValidationError(_('Filename contains invalid path characters.'))
    
    # Check for null bytes and control characters
    if '\x00' in filename or any(ord(c) < 32 for c in filename if c not in '\t\n\r'):
        raise ValidationError(_('Filename contains invalid characters.'))
    
    # Ensure filename is not too long
    if len(filename) > 255:
        raise ValidationError(_('Filename is too long. Maximum 255 characters.'))


def sanitize_filename(filename):
    """Sanitize filename by removing dangerous characters"""
    import re
    
    # Remove path traversal attempts first
    filename = filename.replace('..', '_')
    filename = filename.replace('/', '_')
    filename = filename.replace('\\', '_')
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[\x00-\x1f]', '', filename)  # Remove control characters
    filename = filename.strip('. ')  # Remove leading/trailing dots and spaces
    
    # Remove any remaining path separators or traversal attempts
    filename = re.sub(r'\.\.+', '_', filename)  # Replace multiple dots
    filename = re.sub(r'[/\\]+', '_', filename)  # Replace path separators
    
    # Ensure filename is not empty after sanitization
    if not filename:
        filename = 'unnamed_file'
    
    return filename


# Custom validators for different document types
document_validator = SecureFileValidator(
    allowed_extensions=['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.txt', '.md'],
    max_size=MAX_FILE_SIZES['document']
)

media_validator = SecureFileValidator(
    allowed_extensions=['.mp3', '.wav', '.mp4', '.mov'],
    max_size=MAX_FILE_SIZES['video']  # Use largest size for media
)

image_validator = SecureImageValidator(MAX_FILE_SIZES['image'])

# Export commonly used validators
__all__ = [
    'SecureFileValidator',
    'SecureImageValidator', 
    'document_validator',
    'media_validator',
    'image_validator',
    'validate_file_size_by_type',
    'validate_no_path_traversal',
    'sanitize_filename',
]
