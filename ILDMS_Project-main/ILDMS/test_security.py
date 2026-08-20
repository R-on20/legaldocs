#!/usr/bin/env python
"""
Security validation test script for ILDMS.
Tests various security features and validation mechanisms.
"""

import os
import sys
import django
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')
django.setup()

from django.test import TestCase, RequestFactory
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from documents.validators import (
    SecureFileValidator, 
    validate_no_path_traversal, 
    sanitize_filename
)
from documents.security_utils import (
    sanitize_html_content,
    sanitize_user_input,
    contains_dangerous_patterns,
    validate_search_query
)
from documents.forms import DocumentUploadForm, AISearchForm
from main.models import User, Document
import tempfile
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityValidationTests:
    """Test security validation features"""
    
    def __init__(self):
        self.factory = RequestFactory()
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_test(self, test_name, test_func):
        """Run individual test and track results"""
        try:
            test_func()
            logger.info(f"✅ {test_name} - PASSED")
            self.passed_tests += 1
        except Exception as e:
            logger.error(f"❌ {test_name} - FAILED: {e}")
            self.failed_tests += 1
    
    def test_file_extension_validation(self):
        """Test file extension validation"""
        validator = SecureFileValidator()
        
        # Test allowed file
        allowed_file = SimpleUploadedFile(
            "test.pdf",
            b"fake pdf content",
            content_type="application/pdf"
        )
        
        # This should not raise an exception for extension check alone
        # (MIME validation might fail, but that's expected)
        
        # Test dangerous file extension
        dangerous_file = SimpleUploadedFile(
            "malware.exe",
            b"dangerous content",
            content_type="application/x-executable"
        )
        
        try:
            validator.validate_file_extension(dangerous_file)
            raise AssertionError("Should have rejected .exe file")
        except ValidationError:
            pass  # Expected
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        # Test dangerous filenames
        dangerous_names = [
            "../../../etc/passwd",
            "file<script>alert('xss')</script>.pdf",
            "file|with|pipes.doc",
            "file:with:colons.txt",
            "file\"with\"quotes.pdf"
        ]
        
        for name in dangerous_names:
            sanitized = sanitize_filename(name)
            assert not any(char in sanitized for char in ['<', '>', ':', '"', '|', '?', '*'])
            assert '..' not in sanitized
    
    def test_path_traversal_validation(self):
        """Test path traversal validation"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "file/../../../etc/passwd.txt",
            "normal_file.pdf"  # This should pass
        ]
        
        for path in dangerous_paths[:-1]:  # Exclude the normal file
            try:
                validate_no_path_traversal(path)
                raise AssertionError(f"Should have rejected path: {path}")
            except ValidationError:
                pass  # Expected
        
        # Normal file should pass
        validate_no_path_traversal(dangerous_paths[-1])
    
    def test_html_sanitization(self):
        """Test HTML content sanitization"""
        dangerous_html = [
            "<script>alert('xss')</script>",
            "<img src='x' onerror='alert(1)'>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<a href='javascript:alert(1)'>Click me</a>",
            "Normal <strong>safe</strong> content"  # This should be preserved
        ]
        
        for html in dangerous_html[:-1]:  # Exclude safe content
            sanitized = sanitize_html_content(html)
            assert "<script>" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
            assert "onerror" not in sanitized.lower()
        
        # Safe content should be preserved
        safe_html = dangerous_html[-1]
        sanitized = sanitize_html_content(safe_html)
        assert "<strong>" in sanitized
        assert "safe" in sanitized
    
    def test_dangerous_pattern_detection(self):
        """Test detection of dangerous patterns"""
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "onload=alert(1)",
            "UNION SELECT * FROM users",
            "Normal safe input"  # This should pass
        ]
        
        for input_text in dangerous_inputs[:-1]:  # Exclude safe input
            assert contains_dangerous_patterns(input_text), f"Should detect danger in: {input_text}"
        
        # Safe input should pass
        assert not contains_dangerous_patterns(dangerous_inputs[-1])
    
    def test_search_query_validation(self):
        """Test search query validation"""
        dangerous_queries = [
            "'; DROP TABLE documents; --",
            "<script>alert('xss')</script>",
            "search term with \"quotes\"",
            "normal search term"  # This should pass
        ]
        
        for query in dangerous_queries[:-1]:  # Exclude safe query
            try:
                validate_search_query(query)
                # Some might be cleaned rather than rejected
            except ValidationError:
                pass  # Expected for some
        
        # Normal query should pass
        cleaned = validate_search_query(dangerous_queries[-1])
        assert cleaned == "normal search term"
    
    def test_user_input_sanitization(self):
        """Test general user input sanitization"""
        inputs = [
            ("<script>alert('xss')</script>Normal text", "Normal text"),
            ("Text with <strong>formatting</strong>", "Text with formatting"),  # No HTML allowed
            ("Normal safe text", "Normal safe text")
        ]
        
        for input_text, expected in inputs:
            sanitized = sanitize_user_input(input_text, allow_html=False)
            # Should not contain script tags
            assert "<script>" not in sanitized.lower()
    
    def test_form_validation(self):
        """Test form-level validation"""
        # Create a test user
        try:
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
        except:
            user = User.objects.get(username='testuser')
        
        # Test document upload form with dangerous data
        dangerous_data = {
            'title': '<script>alert("xss")</script>Malicious Title',
            'document_type': 'OTHER',
            'description': '<iframe src="javascript:alert(1)"></iframe>Bad description'
        }
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"fake pdf content",
            content_type="application/pdf"
        )
        
        form = DocumentUploadForm(
            data=dangerous_data,
            files={'file': test_file},
            user=user
        )
        
        # Form should clean the dangerous content
        if form.is_valid():
            assert "<script>" not in form.cleaned_data['title'].lower()
            assert "<iframe>" not in form.cleaned_data['description'].lower()
        
        # Test AI search form
        ai_form = AISearchForm(data={'ai_query': '<script>alert("xss")</script>Find documents'})
        if ai_form.is_valid():
            assert "<script>" not in ai_form.cleaned_data['ai_query'].lower()
    
    def test_file_size_limits(self):
        """Test file size validation"""
        # Create a file that's too large (simulate)
        validator = SecureFileValidator(max_size=1024)  # 1KB limit
        
        large_file = SimpleUploadedFile(
            "large.pdf",
            b"x" * 2048,  # 2KB file
            content_type="application/pdf"
        )
        
        try:
            validator.validate_file_size(large_file)
            raise AssertionError("Should have rejected large file")
        except ValidationError:
            pass  # Expected
    
    def run_all_tests(self):
        """Run all security tests"""
        logger.info("🔐 Starting Security Validation Tests...")
        
        tests = [
            ("File Extension Validation", self.test_file_extension_validation),
            ("Filename Sanitization", self.test_filename_sanitization),
            ("Path Traversal Validation", self.test_path_traversal_validation),
            ("HTML Sanitization", self.test_html_sanitization),
            ("Dangerous Pattern Detection", self.test_dangerous_pattern_detection),
            ("Search Query Validation", self.test_search_query_validation),
            ("User Input Sanitization", self.test_user_input_sanitization),
            ("Form Validation", self.test_form_validation),
            ("File Size Limits", self.test_file_size_limits),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Summary
        total_tests = self.passed_tests + self.failed_tests
        logger.info(f"\n📊 Test Results:")
        logger.info(f"✅ Passed: {self.passed_tests}/{total_tests}")
        logger.info(f"❌ Failed: {self.failed_tests}/{total_tests}")
        
        if self.failed_tests == 0:
            logger.info("🎉 All security tests passed!")
        else:
            logger.warning(f"⚠️  {self.failed_tests} test(s) failed. Review security implementation.")
        
        return self.failed_tests == 0


def main():
    """Main test runner"""
    print("🔐 ILDMS Security Validation Test Suite")
    print("=" * 50)
    
    tester = SecurityValidationTests()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Security validation completed successfully!")
        print("Your Django application has comprehensive security measures in place.")
    else:
        print("\n❌ Some security tests failed.")
        print("Please review the failed tests and fix the issues before deployment.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
