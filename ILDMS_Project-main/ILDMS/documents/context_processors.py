"""
Context processor for document permissions
"""
from .views import can_manage_documents

def document_permissions(request):
    """Add document permissions to template context"""
    if request.user.is_authenticated:
        return {
            'user_can_manage_documents': can_manage_documents(request.user),
            'user_can_create_documents': can_manage_documents(request.user),
            'user_can_upload_documents': can_manage_documents(request.user),
            'user_can_edit_documents': can_manage_documents(request.user),
            'user_can_delete_documents': can_manage_documents(request.user),
            'user_can_create_versions': can_manage_documents(request.user),
        }
    return {
        'user_can_manage_documents': False,
        'user_can_create_documents': False,
        'user_can_upload_documents': False,
        'user_can_edit_documents': False,
        'user_can_delete_documents': False,
        'user_can_create_versions': False,
    }
