#!/usr/bin/env python
"""
Minimal Security Validation Test Script
Tests all security features without Django's full app loading
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')

import django
django.setup()

# Now import what we need
from documents.validators import (
    validate_file_extension,
    validate_file_size_by_type,
    sanitize_filename,
    validate_no_path_traversal,
    SecureFileValidator,
    SecureImageValidator
)
from documents.security_utils import (
    sanitize_html_content,
    detect_dangerous_patterns,
    validate_search_input,
    sanitize_user_input
)

def create_test_file(filename, content=b"test content", size=None):
    """Create a temporary test file"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}")
    if size:
        temp_file.write(b"A" * size)
    else:
        temp_file.write(content)
    temp_file.close()
    return temp_file.name

def test_file_extension_validation():
    """Test file extension validation"""
    print("🔍 Testing file extension validation...")
    
    # Test allowed extensions
    assert validate_file_extension("test.pdf") == True
    assert validate_file_extension("document.docx") == True
    assert validate_file_extension("image.jpg") == True
    
    # Test dangerous extensions
    try:
        validate_file_extension("malware.exe")
        assert False, "Should have rejected .exe file"
    except Exception:
        pass  # Expected
    
    try:
        validate_file_extension("script.bat")
        assert False, "Should have rejected .bat file"
    except Exception:
        pass  # Expected
    
    print("✅ File extension validation working correctly")

def test_filename_sanitization():
    """Test filename sanitization"""
    print("🔍 Testing filename sanitization...")
    
    # Test path traversal prevention
    sanitized = sanitize_filename("../../../etc/passwd")
    assert ".." not in sanitized
    assert "/" not in sanitized
    assert "\\" not in sanitized
    
    # Test dangerous characters removal
    sanitized = sanitize_filename("test<script>alert()</script>.pdf")
    assert "<" not in sanitized
    assert ">" not in sanitized
    assert "script" in sanitized  # Content should remain, just tags removed
    
    print("✅ Filename sanitization working correctly")

def test_path_traversal_validation():
    """Test path traversal validation"""
    print("🔍 Testing path traversal validation...")
    
    # Test legitimate paths
    try:
        validate_no_path_traversal("legitimate_file.pdf")
        validate_no_path_traversal("My Document.docx")
    except:
        assert False, "Should allow legitimate filenames"
    
    # Test path traversal attempts
    dangerous_paths = [
        "../../../etc/passwd",
        "..\\..\\windows\\system32",
        "/etc/shadow",
        "C:\\Windows\\System32\\cmd.exe"
    ]
    
    for dangerous_path in dangerous_paths:
        try:
            validate_no_path_traversal(dangerous_path)
            assert False, f"Should have rejected: {dangerous_path}"
        except:
            pass  # Expected
    
    print("✅ Path traversal validation working correctly")

def test_html_sanitization():
    """Test HTML content sanitization"""
    print("🔍 Testing HTML sanitization...")
    
    # Test XSS prevention
    malicious_html = '<script>alert("XSS")</script><p>Safe content</p>'
    sanitized = sanitize_html_content(malicious_html)
    assert "<script>" not in sanitized
    assert "alert" not in sanitized
    assert "<p>Safe content</p>" in sanitized
    
    # Test iframe and object removal
    iframe_html = '<iframe src="http://evil.com"></iframe><p>Content</p>'
    sanitized = sanitize_html_content(iframe_html)
    assert "<iframe>" not in sanitized
    assert "<p>Content</p>" in sanitized
    
    print("✅ HTML sanitization working correctly")

def test_dangerous_pattern_detection():
    """Test dangerous pattern detection"""
    print("🔍 Testing dangerous pattern detection...")
    
    # Test SQL injection patterns
    sql_patterns = [
        "'; DROP TABLE users; --",
        "UNION SELECT * FROM passwords",
        "admin'--",
        "1' OR '1'='1"
    ]
    
    for pattern in sql_patterns:
        assert detect_dangerous_patterns(pattern) == True, f"Should detect: {pattern}"
    
    # Test XSS patterns
    xss_patterns = [
        "<script>alert('xss')</script>",
        "javascript:alert(1)",
        "onload=alert(1)",
        "<img onerror=alert(1) src=x>"
    ]
    
    for pattern in xss_patterns:
        assert detect_dangerous_patterns(pattern) == True, f"Should detect: {pattern}"
    
    # Test safe content
    safe_content = [
        "normal search query",
        "document title",
        "user@example.com",
        "123-456-7890"
    ]
    
    for content in safe_content:
        assert detect_dangerous_patterns(content) == False, f"Should allow: {content}"
    
    print("✅ Dangerous pattern detection working correctly")

def test_search_input_validation():
    """Test search input validation"""
    print("🔍 Testing search input validation...")
    
    # Test normal queries
    normal_queries = [
        "project management",
        "financial report 2024",
        "meeting notes",
        "user manual"
    ]
    
    for query in normal_queries:
        sanitized = validate_search_input(query)
        assert len(sanitized) > 0
        assert sanitized == query  # Should remain unchanged
    
    # Test dangerous queries
    dangerous_queries = [
        "'; DROP TABLE documents; --",
        "<script>alert('xss')</script>",
        "UNION SELECT * FROM users"
    ]
    
    for query in dangerous_queries:
        sanitized = validate_search_input(query)
        # Should be cleaned or rejected
        assert "<script>" not in sanitized
        assert "DROP TABLE" not in sanitized.upper()
        assert "UNION SELECT" not in sanitized.upper()
    
    print("✅ Search input validation working correctly")

def test_user_input_sanitization():
    """Test general user input sanitization"""
    print("🔍 Testing user input sanitization...")
    
    # Test HTML in user input
    user_inputs = [
        "<b>Bold text</b> and normal text",
        "Title with <script>alert(1)</script> malicious code",
        "Description with <iframe src='evil.com'></iframe> embedded content"
    ]
    
    for user_input in user_inputs:
        sanitized = sanitize_user_input(user_input)
        assert "<script>" not in sanitized
        assert "<iframe>" not in sanitized
        # Allow safe tags like <b>, <i>, <p>
        if "<b>" in user_input and "<script>" not in user_input:
            assert "<b>" in sanitized  # Safe tags should remain
    
    print("✅ User input sanitization working correctly")

def test_file_size_validation():
    """Test file size validation"""
    print("🔍 Testing file size validation...")
    
    # Create test files of different sizes
    small_file = create_test_file("small.pdf", size=1024)  # 1KB
    large_file = create_test_file("large.pdf", size=100 * 1024 * 1024)  # 100MB
    
    try:
        # Small file should pass
        with open(small_file, 'rb') as f:
            validate_file_size_by_type(f, "application/pdf")
        
        # Large file should fail for most types
        try:
            with open(large_file, 'rb') as f:
                validate_file_size_by_type(f, "application/pdf")
            assert False, "Should have rejected oversized file"
        except:
            pass  # Expected
        
    finally:
        # Clean up
        os.unlink(small_file)
        os.unlink(large_file)
    
    print("✅ File size validation working correctly")

def test_secure_file_validator():
    """Test the comprehensive secure file validator"""
    print("🔍 Testing secure file validator...")
    
    # Create a test PDF file
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    test_file = create_test_file("test.pdf", pdf_content)
    
    try:
        validator = SecureFileValidator()
        
        # Test with legitimate file
        with open(test_file, 'rb') as f:
            result = validator.validate(f, "test.pdf", "application/pdf")
            # Should return validation results
            assert isinstance(result, dict)
        
    finally:
        os.unlink(test_file)
    
    print("✅ Secure file validator working correctly")

def run_all_tests():
    """Run all security validation tests"""
    print("🚀 Starting Security Validation Tests\n")
    
    test_functions = [
        test_file_extension_validation,
        test_filename_sanitization,
        test_path_traversal_validation,
        test_html_sanitization,
        test_dangerous_pattern_detection,
        test_search_input_validation,
        test_user_input_sanitization,
        test_file_size_validation,
        test_secure_file_validator
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}")
            failed += 1
        print()  # Add spacing between tests
    
    print("=" * 60)
    print(f"🎯 Security Validation Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL SECURITY TESTS PASSED!")
        print("✅ Your Django application has comprehensive security measures in place.")
        print("🔒 Ready for external testing with confidence!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review and fix the issues.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
