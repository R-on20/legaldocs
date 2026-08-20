#!/usr/bin/env python
"""
Test script for permanent delete audit logging functionality
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')

django.setup()

from django.contrib.auth import get_user_model
from main.models import Document, AuditLog
from django.utils import timezone
from django.test import RequestFactory
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()

def test_permanent_delete_audit_logging():
    """Test that permanent delete creates audit logs properly"""
    print("=" * 60)
    print("TESTING PERMANENT DELETE AUDIT LOGGING")
    print("=" * 60)
    
    # Get or create a test user
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                is_superuser=True
            )
        print(f"✅ Using test user: {user.username}")
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return False
    
    # Create a test document
    try:
        from django.core.files.base import ContentFile
        
        test_document = Document.objects.create(
            title="Test Document for Permanent Delete",
            document_type=Document.DocType.OTHER,
            uploaded_by=user,
            is_archived=True,
            archived_at=timezone.now(),
            archived_by=user,
            description="Test document for permanent delete audit logging",
            confidential=False
        )
        
        # Add a test file
        test_document.file.save(
            'test_document.txt',
            ContentFile(b'This is test content for permanent delete testing')
        )
        test_document.save()
        
        print(f"✅ Created test document: ID={test_document.id}, Title='{test_document.title}'")
    except Exception as e:
        print(f"❌ Failed to create test document: {e}")
        return False
    
    # Count audit logs before deletion
    initial_audit_count = AuditLog.objects.count()
    print(f"📊 Initial audit log count: {initial_audit_count}")
    
    # Count audit logs for this specific document
    doc_audit_count_before = AuditLog.objects.filter(document_id=test_document.id).count()
    print(f"📊 Audit logs for this document before delete: {doc_audit_count_before}")
    
    # Create a mock request with messages support
    factory = RequestFactory()
    request = factory.post(f'/documents/{test_document.id}/delete-permanent/')
    request.user = user
    request.META['REMOTE_ADDR'] = '127.0.0.1'
    request.META['HTTP_USER_AGENT'] = 'Test Script User Agent'
    request.session = type('MockSession', (), {'session_key': 'test_session_key'})()
    
    # Mock the messages framework to avoid errors
    from unittest.mock import Mock
    request._messages = Mock()
    
    # Store document info for verification
    doc_id = test_document.id
    doc_title = test_document.title
    doc_type = test_document.get_document_type_display()
    
    print(f"🔄 Attempting to delete document {doc_id}: {doc_title}")
    
    try:
        # Import the view and simulate the delete operation
        from documents.views import DocumentPermanentDeleteView
        
        # Create view instance
        view = DocumentPermanentDeleteView()
        view.setup(request)
        view.kwargs = {'pk': test_document.id}
        
        # Call the delete method
        response = view.delete(request, pk=test_document.id)
        
        print("✅ Delete method executed without errors")
        
    except Exception as e:
        print(f"❌ Delete method failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Check if document was deleted
    try:
        Document.objects.get(id=doc_id)
        print("❌ Document still exists after delete!")
        return False
    except Document.DoesNotExist:
        print("✅ Document was successfully deleted")
    
    # Check if audit log was created
    final_audit_count = AuditLog.objects.count()
    print(f"📊 Final audit log count: {final_audit_count}")
    print(f"📊 Audit logs created: {final_audit_count - initial_audit_count}")
    
    # Look for audit logs for the deleted document
    delete_audit_logs = AuditLog.objects.filter(
        document_id=doc_id,
        action='DELETE'
    )
    
    print(f"🔍 Found {delete_audit_logs.count()} DELETE audit logs for document {doc_id}")
    
    if delete_audit_logs.exists():
        for log in delete_audit_logs:
            print(f"✅ DELETE Audit Log found:")
            print(f"   - ID: {log.id}")
            print(f"   - User: {log.user.username if log.user else 'None'}")
            print(f"   - Document ID: {log.document_id}")
            print(f"   - Document Title: {log.document_title}")
            print(f"   - Document Type: {log.document_type}")
            print(f"   - Action: {log.action}")
            print(f"   - Timestamp: {log.timestamp}")
            print(f"   - IP Address: {log.ip_address}")
            print(f"   - Additional Info: {log.additional_info}")
        return True
    else:
        print("❌ No DELETE audit log found for the deleted document!")
        
        # Check all recent audit logs to see what was created
        recent_logs = AuditLog.objects.order_by('-timestamp')[:10]
        print("\n🔍 Recent audit logs (last 10):")
        for log in recent_logs:
            print(f"   - {log.timestamp}: {log.user.username if log.user else 'None'} "
                  f"{log.action} doc_{log.document_id} ({log.document_title})")
        
        return False

def cleanup_test_data():
    """Clean up any remaining test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Delete test documents
    test_docs = Document.objects.filter(title__contains="Test Document for Permanent Delete")
    deleted_count = test_docs.count()
    test_docs.delete()
    print(f"   Deleted {deleted_count} test documents")
    
    # Optionally delete test audit logs
    # test_logs = AuditLog.objects.filter(document_title__contains="Test Document for Permanent Delete")
    # log_count = test_logs.count() 
    # test_logs.delete()
    # print(f"   Deleted {log_count} test audit logs")

if __name__ == '__main__':
    try:
        success = test_permanent_delete_audit_logging()
        
        if success:
            print("\n🎉 TEST PASSED: Permanent delete audit logging is working correctly!")
        else:
            print("\n❌ TEST FAILED: Permanent delete audit logging is not working properly!")
            
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Don't cleanup automatically - let's examine the data
        print("\n💡 Test complete. Audit logs preserved for examination.")
        print("   You can check the audit log in the admin or web interface.")
