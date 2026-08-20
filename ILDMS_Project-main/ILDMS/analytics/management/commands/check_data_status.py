from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import Document, AuditLog, User
from analytics.models import SearchQuery, UserActivity, SystemMetrics


class Command(BaseCommand):
    help = 'Check current system data state'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== SYSTEM DATA STATUS ==='))
        
        # Document status
        doc_count = Document.objects.count()
        self.stdout.write(f"📄 Documents in DB: {doc_count}")
        
        # Audit log status
        audit_count = AuditLog.objects.count()
        self.stdout.write(f"📊 Audit Logs: {audit_count}")
        
        if audit_count > 0:
            # Unique documents from audit logs
            unique_docs = AuditLog.objects.values('document_id').distinct().count()
            self.stdout.write(f"🔗 Unique Document IDs in audit logs: {unique_docs}")
            
            # Recent activities
            recent = AuditLog.objects.order_by('-timestamp')[:5]
            self.stdout.write("📈 Recent Activities:")
            for log in recent:
                self.stdout.write(f"  • {log.timestamp.strftime('%Y-%m-%d %H:%M')} - {log.action} - {log.document_title or 'Unknown'}")
            
            # Action breakdown
            actions = AuditLog.objects.values('action').distinct()
            self.stdout.write("🎯 Action Types Available:")
            for action in actions:
                count = AuditLog.objects.filter(action=action['action']).count()
                self.stdout.write(f"  • {action['action']}: {count}")
        
        # User status  
        user_count = User.objects.count()
        self.stdout.write(f"👥 Users: {user_count}")
        
        # Analytics data
        self.stdout.write(f"🔍 Search Queries: {SearchQuery.objects.count()}")
        self.stdout.write(f"📋 User Activities: {UserActivity.objects.count()}")
        self.stdout.write(f"⚙️ System Metrics: {SystemMetrics.objects.count()}")
        
        self.stdout.write(self.style.SUCCESS('=== END STATUS REPORT ==='))
