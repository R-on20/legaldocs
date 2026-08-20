import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')
django.setup()

from main.models import Document, AuditLog, User

print("=== SYSTEM DATA STATUS ===")

# Document status
doc_count = Document.objects.count()
print(f"📄 Documents in DB: {doc_count}")

# Audit log status  
audit_count = AuditLog.objects.count()
print(f"📊 Audit Logs: {audit_count}")

if audit_count > 0:
    # Recent activities
    recent = AuditLog.objects.order_by('-timestamp')[:3]
    print("📈 Recent Activities:")
    for log in recent:
        print(f"  • {log.timestamp.strftime('%Y-%m-%d %H:%M')} - {log.action} - {log.document_title or 'Unknown'}")
    
    # Action breakdown
    actions = ['CREATE', 'VIEW', 'DOWNLOAD', 'UPDATE', 'DELETE', 'ARCHIVE']
    print("🎯 Action Counts:")
    for action in actions:
        count = AuditLog.objects.filter(action=action).count()
        if count > 0:
            print(f"  • {action}: {count}")

# User status
user_count = User.objects.count()
print(f"👥 Users: {user_count}")

print("=== END REPORT ===")
