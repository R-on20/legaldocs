#!/usr/bin/env python
"""
Test script to debug upload issues
"""
import os
import sys
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile

User = get_user_model()

def test_upload_debug():
    print("=== UPLOAD DEBUG TEST ===")
    
    # Create a test client
    client = Client()
    
    # Get or create a test user
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ No active users found")
        return
    
    print(f"✓ Testing with user: {user.username}")
    
    # Login the user
    client.force_login(user)
    
    # Create a test file
    test_content = b"This is a test document for upload debugging"
    test_file = SimpleUploadedFile(
        "test_upload_debug.txt", 
        test_content, 
        content_type="text/plain"
    )
    
    # Test upload data
    upload_data = {
        'title': 'Debug Test Document',
        'description': 'Testing upload functionality',
        'document_type': 'report',
        'file': test_file,
    }
    
    print("📤 Attempting upload...")
    
    # Try upload with AJAX headers
    response = client.post('/upload/', upload_data, 
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                          HTTP_X_CSRFTOKEN='test')
    
    print(f"Response status: {response.status_code}")
    print(f"Response content type: {response.get('Content-Type', 'Not set')}")
    print(f"Response content length: {len(response.content)}")
    
    if response.status_code == 200:
        try:
            import json
            response_data = json.loads(response.content)
            print(f"JSON Response: {response_data}")
        except json.JSONDecodeError:
            print(f"Non-JSON Response: {response.content.decode()[:500]}...")
    else:
        print(f"❌ Upload failed with status {response.status_code}")
        print(f"Response: {response.content.decode()[:500]}...")
    
    # Also test regular form submission
    print("\n📤 Testing regular form submission...")
    test_file2 = SimpleUploadedFile(
        "test_upload_debug2.txt", 
        test_content, 
        content_type="text/plain"
    )
    upload_data['file'] = test_file2
    
    response2 = client.post('/upload/', upload_data)
    print(f"Regular form response status: {response2.status_code}")
    if response2.status_code == 302:
        print(f"✓ Redirect to: {response2.get('Location', 'Unknown')}")
    else:
        print(f"Response: {response2.content.decode()[:500]}...")

if __name__ == "__main__":
    test_upload_debug()
