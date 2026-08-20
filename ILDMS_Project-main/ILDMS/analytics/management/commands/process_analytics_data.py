from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
import os
import json

from main.models import Document, AuditLog, User
from analytics.models import AnalyticsSnapshot, UserActivity, SystemMetrics, SearchQuery


class Command(BaseCommand):
    help = 'Process and rebuild analytics data from existing system data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rebuild-documents',
            action='store_true',
            help='Attempt to rebuild document records from media files',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to process for analytics (default: 30)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting analytics data processing...'))
        
        # Check current state
        self.check_current_state()
        
        if options['rebuild_documents']:
            self.rebuild_documents()
        
        # Process analytics data
        self.process_analytics_data(options['days'])
        
        self.stdout.write(self.style.SUCCESS('Analytics data processing complete!'))

    def check_current_state(self):
        """Check and report current system state"""
        self.stdout.write("=== CURRENT SYSTEM STATE ===")
        self.stdout.write(f"Documents: {Document.objects.count()}")
        self.stdout.write(f"Audit Logs: {AuditLog.objects.count()}")
        self.stdout.write(f"Users: {User.objects.count()}")
        self.stdout.write(f"Search Queries: {SearchQuery.objects.count()}")
        self.stdout.write(f"User Activities: {UserActivity.objects.count()}")
        self.stdout.write(f"System Metrics: {SystemMetrics.objects.count()}")
        
        # Check media files
        media_path = 'media/documents'
        if os.path.exists(media_path):
            file_count = sum([len(files) for r, d, files in os.walk(media_path)])
            self.stdout.write(f"Files in media/documents: {file_count}")
        
    def rebuild_documents(self):
        """Attempt to rebuild document records from audit logs and media files"""
        self.stdout.write("=== REBUILDING DOCUMENTS ===")
        
        # Get unique document IDs from audit logs
        document_ids = AuditLog.objects.values_list('document_id', flat=True).distinct()
        document_ids = [doc_id for doc_id in document_ids if doc_id is not None]
        
        self.stdout.write(f"Found {len(document_ids)} unique document IDs in audit logs")
        
        # Check which documents are missing
        existing_doc_ids = set(Document.objects.values_list('id', flat=True))
        missing_doc_ids = set(document_ids) - existing_doc_ids
        
        self.stdout.write(f"Missing document records: {len(missing_doc_ids)}")
        
        if missing_doc_ids:
            self.stdout.write(self.style.WARNING(
                "Note: Document records are missing but audit logs reference them. "
                "This might indicate data corruption or accidental deletion."
            ))
            
            # Get details about missing documents from audit logs
            for doc_id in list(missing_doc_ids)[:10]:  # Show first 10
                logs = AuditLog.objects.filter(document_id=doc_id).order_by('timestamp')
                if logs:
                    first_log = logs.first()
                    self.stdout.write(f"  Document ID {doc_id}: '{first_log.document_title}' ({first_log.document_type})")

    def process_analytics_data(self, days):
        """Process existing data to create analytics insights"""
        self.stdout.write(f"=== PROCESSING ANALYTICS DATA (Last {days} days) ===")
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Process daily snapshots
        self.create_daily_snapshots(start_date, end_date)
        
        # Process user activity from audit logs
        self.process_user_activity(start_date, end_date)
        
        # Update system metrics
        self.update_system_metrics()
        
    def create_daily_snapshots(self, start_date, end_date):
        """Create daily analytics snapshots"""
        self.stdout.write("Creating daily snapshots...")
        
        current_date = start_date.date()
        snapshots_created = 0
        
        while current_date <= end_date.date():
            snapshot, created = AnalyticsSnapshot.objects.get_or_create(
                date=current_date,
                defaults={
                    'total_documents': Document.objects.count(),
                    'active_documents': Document.objects.filter(is_archived=False).count(),
                    'archived_documents': Document.objects.filter(is_archived=True).count(),
                    'total_users': User.objects.count(),
                    'active_users': User.objects.filter(last_login__date=current_date).count(),
                }
            )
            
            # Update daily metrics
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())
            
            # Documents uploaded on this day
            uploads_today = AuditLog.objects.filter(
                action='CREATE',
                timestamp__range=[day_start, day_end]
            ).count()
            
            # Document views on this day
            views_today = AuditLog.objects.filter(
                action='VIEW',
                timestamp__range=[day_start, day_end]
            ).count()
            
            # Searches on this day  
            searches_today = SearchQuery.objects.filter(
                timestamp__date=current_date
            ).count()
            
            # Update snapshot
            snapshot.documents_uploaded_today = uploads_today
            snapshot.document_views_today = views_today
            snapshot.searches_today = searches_today
            
            # Document type distribution
            doc_types = {}
            for action_log in AuditLog.objects.filter(
                action='CREATE',
                timestamp__range=[day_start, day_end]
            ):
                doc_type = action_log.document_type or 'Unknown'
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            snapshot.document_type_distribution = doc_types
            snapshot.save()
            
            if created:
                snapshots_created += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f"Created {snapshots_created} new daily snapshots")

    def process_user_activity(self, start_date, end_date):
        """Process user activity from audit logs"""
        self.stdout.write("Processing user activity...")
        
        # Map audit log actions to user activity types
        action_mapping = {
            'CREATE': 'DOCUMENT_UPLOAD',
            'VIEW': 'DOCUMENT_VIEW', 
            'DOWNLOAD': 'DOCUMENT_DOWNLOAD',
            'UPDATE': 'DOCUMENT_EDIT',
        }
        
        activities_created = 0
        
        for log in AuditLog.objects.filter(
            timestamp__range=[start_date, end_date],
            user__isnull=False
        ):
            if log.action in action_mapping:
                activity_type = action_mapping[log.action]
                
                # Check if activity already exists
                existing = UserActivity.objects.filter(
                    user=log.user,
                    activity_type=activity_type,
                    timestamp=log.timestamp
                ).exists()
                
                if not existing:
                    UserActivity.objects.create(
                        user=log.user,
                        activity_type=activity_type,
                        timestamp=log.timestamp,
                        ip_address=log.ip_address,
                        user_agent=log.user_agent,
                        additional_data={
                            'document_id': log.document_id,
                            'document_title': log.document_title,
                            'original_action': log.action
                        }
                    )
                    activities_created += 1
        
        self.stdout.write(f"Created {activities_created} user activity records")

    def update_system_metrics(self):
        """Update system-wide metrics"""
        self.stdout.write("Updating system metrics...")
        
        metrics = {
            'total_documents': Document.objects.count(),
            'total_users': User.objects.count(),
            'total_audit_logs': AuditLog.objects.count(),
            'total_searches': SearchQuery.objects.count(),
            'active_users_30_days': User.objects.filter(
                last_login__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'documents_this_month': AuditLog.objects.filter(
                action='CREATE',
                timestamp__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'top_document_types': list(
                AuditLog.objects.filter(action='CREATE')
                .values('document_type')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
            'most_active_users': list(
                AuditLog.objects.values('user__username')
                .annotate(activity_count=Count('id'))
                .order_by('-activity_count')[:10]
            )
        }
        
        for metric_name, metric_value in metrics.items():
            SystemMetrics.objects.update_or_create(
                metric_name=metric_name,
                defaults={
                    'metric_value': json.dumps(metric_value),
                    'description': f'Auto-generated metric: {metric_name}'
                }
            )
        
        self.stdout.write(f"Updated {len(metrics)} system metrics")
