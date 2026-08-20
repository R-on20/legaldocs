from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import Document, AuditLog
from django.utils import timezone
import os
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Restore Document records from audit logs and physical files'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting document restoration from audit logs...'))
        
        # Get all CREATE actions from audit logs that represent document uploads
        create_logs = AuditLog.objects.filter(action='CREATE').order_by('timestamp')
        
        restored_count = 0
        skipped_count = 0
        
        for log in create_logs:
            # Extract document info from the log
            if log.action == 'CREATE' and log.document_title:
                try:
                    # Get the document name from the log
                    doc_name = log.document_title
                    
                    if not doc_name:
                        continue
                        
                    # Check if document already exists
                    if Document.objects.filter(title=doc_name).exists():
                        skipped_count += 1
                        continue
                    
                    # Try to find the physical file
                    media_root = settings.MEDIA_ROOT
                    documents_dir = os.path.join(media_root, 'documents')
                    
                    potential_files = []
                    if os.path.exists(documents_dir):
                        for filename in os.listdir(documents_dir):
                            if doc_name.lower() in filename.lower() or filename.lower() in doc_name.lower():
                                potential_files.append(filename)
                    
                    if not potential_files:
                        # Create document record without file
                        doc_file_path = f"documents/{doc_name}"
                    else:
                        # Use the first matching file
                        doc_file_path = f"documents/{potential_files[0]}"
                    
                    # Create the document record
                    document = Document.objects.create(
                        title=doc_name,
                        description=f"Restored from audit log - {log.action}",
                        file=doc_file_path,
                        uploaded_by=log.user,
                        # Don't set uploaded_at and modified_at - they auto-populate
                        # Don't set is_active - field doesn't exist, use is_archived instead
                        is_archived=False
                    )
                    
                    restored_count += 1
                    self.stdout.write(f"✓ Restored: {doc_name}")
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error restoring {log.document_title}: {str(e)}"))
                    continue
        
        # Also check for physical files without matching audit logs
        orphaned_count = 0
        media_root = settings.MEDIA_ROOT
        documents_dir = os.path.join(media_root, 'documents')
        
        if os.path.exists(documents_dir):
            for filename in os.listdir(documents_dir):
                if os.path.isfile(os.path.join(documents_dir, filename)):
                    # Check if we already have a document for this file
                    file_path = f"documents/{filename}"
                    if not Document.objects.filter(file=file_path).exists():
                        # Create document from orphaned file
                        title = os.path.splitext(filename)[0].replace('_', ' ').title()
                        
                        # Try to find a user from recent logs
                        recent_user = User.objects.first()
                        if AuditLog.objects.exists():
                            recent_log = AuditLog.objects.order_by('-timestamp').first()
                            if recent_log.user:
                                recent_user = recent_log.user
                        
                        document = Document.objects.create(
                            title=title,
                            description=f"Restored from orphaned file: {filename}",
                            file=file_path,
                            uploaded_by=recent_user,
                            # Don't set uploaded_at and modified_at - they auto-populate
                            is_archived=False
                        )
                        
                        orphaned_count += 1
                        self.stdout.write(f"✓ Restored orphaned file: {filename}")
        
        self.stdout.write(self.style.SUCCESS(f'\n=== RESTORATION COMPLETE ==='))
        self.stdout.write(f"📄 Documents restored from logs: {restored_count}")
        self.stdout.write(f"📁 Orphaned files restored: {orphaned_count}")
        self.stdout.write(f"⏭️ Skipped (already exist): {skipped_count}")
        self.stdout.write(f"📊 Total documents now: {Document.objects.count()}")
