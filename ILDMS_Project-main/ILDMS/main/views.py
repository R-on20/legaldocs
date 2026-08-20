from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db import models
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

User = get_user_model()

# Import models from main app
from .models import Document, DocumentVersion, AuditLog

# Import analytics models if available
try:
    from analytics.models import SearchQuery, UserActivity
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Modern dashboard view with statistics, quick actions, and navigation
    """
    template_name = 'main/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Role-based context (matching navigation logic)
        context['can_upload'] = user.role in ['LAWYER', 'ADMIN', 'PARALEGAL', 'SENIOR_PARALEGAL']
        context['can_create'] = user.role in ['LAWYER', 'ADMIN', 'PARALEGAL', 'SENIOR_PARALEGAL']
        context['can_view_admin'] = user.role in ['ADMIN', 'PARALEGAL', 'SENIOR_PARALEGAL'] or user.is_staff
        context['can_view_audit'] = user.role in ['ADMIN', 'PARALEGAL', 'SENIOR_PARALEGAL'] or user.is_staff
        context['can_manage_users'] = user.role == 'ADMIN' or user.is_staff
        
        # Document statistics
        docs_qs = Document.objects.all()
        if not user.has_perm('documents.can_view_confidential'):
            docs_qs = docs_qs.filter(confidential=False)
                
        context['total_documents'] = docs_qs.count()
        context['active_documents'] = docs_qs.filter(is_archived=False).count()
        context['archived_documents'] = docs_qs.filter(is_archived=True).count()
        context['pending_review'] = docs_qs.filter(status='REVIEW').count()
        
        # Document type breakdown
        context['document_types'] = docs_qs.values('document_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]  # Top 5 document types
        
        # Recent activity
        context['recent_documents'] = docs_qs.order_by('-uploaded_at')[:5]
        
        # Recent uploads by current user
        context['my_recent_documents'] = docs_qs.filter(
            uploaded_by=user
        ).order_by('-uploaded_at')[:3]
        
        # Activity statistics for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        context['recent_uploads'] = docs_qs.filter(
            uploaded_at__gte=thirty_days_ago
        ).count()
        
        # Storage statistics - calculate using file system access
        try:
            import os
            total_size = 0
            for doc in docs_qs:
                if doc.file and hasattr(doc.file, 'path'):
                    try:
                        if os.path.exists(doc.file.path):
                            total_size += os.path.getsize(doc.file.path)
                    except (OSError, ValueError):
                        continue  # Skip files that can't be accessed
            context['total_storage_mb'] = round(total_size / (1024 * 1024), 2)
        except Exception:
            context['total_storage_mb'] = 0
        
        # User statistics (if user has permission)
        if context['can_manage_users']:
            context['total_users'] = User.objects.count()
            context['active_users'] = User.objects.filter(is_active=True).count()
            context['recent_users'] = User.objects.filter(
                date_joined__gte=timezone.now() - timedelta(days=30)
            ).count()
        
        # Recent versions (if user can view them and DocumentVersion exists)
        if context['can_view_admin'] and DocumentVersion:
            context['recent_versions'] = DocumentVersion.objects.select_related(
                'document', 'created_by'
            ).order_by('-created_at')[:5]
        else:
            context['recent_versions'] = []
        
        # Analytics data for dashboard overview
        if ANALYTICS_AVAILABLE:
            # Calculate analytics for the last 30 days
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            
            # Search analytics
            context['total_searches'] = SearchQuery.objects.filter(
                timestamp__range=[start_date, end_date]
            ).count()
            
            # View analytics (from audit logs)
            context['total_views'] = AuditLog.objects.filter(
                action='VIEW',
                timestamp__range=[start_date, end_date]
            ).count()
            
            # Download analytics (from audit logs)
            context['total_downloads'] = AuditLog.objects.filter(
                action='DOWNLOAD',
                timestamp__range=[start_date, end_date]
            ).count()
            
            # Active users count (users who performed any action in the last 30 days)
            context['active_users_count'] = AuditLog.objects.filter(
                timestamp__range=[start_date, end_date]
            ).values('user').distinct().count()
            
        else:
            # Default values if analytics app is not available
            context.update({
                'total_searches': 0,
                'total_views': 0,
                'total_downloads': 0,
                'active_users_count': 0,
            })
        
        # Add draft documents count (if the field exists)
        try:
            context['draft_documents'] = docs_qs.filter(status='DRAFT').count()
        except:
            context['draft_documents'] = 0
        
        return context


@login_required
def dashboard_stats_api(request):
    """
    API endpoint for dashboard statistics (for charts and dynamic updates)
    """
    from django.http import JsonResponse
    from django.db.models.functions import TruncMonth
    
    user = request.user
    
    # Import the correct Document model
    from documents.models import Document
    
    docs_qs = Document.objects.all()
    
    if not user.has_perm('documents.can_view_confidential'):
        docs_qs = docs_qs.filter(confidential=False)
    
    # Monthly upload statistics for the last 12 months
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)
    
    monthly_data = docs_qs.filter(
        uploaded_at__range=[start_date, end_date]
    ).annotate(
        month=TruncMonth('uploaded_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Create complete 12-month dataset
    labels = []
    data = []
    current_date = start_date.replace(day=1)
    data_dict = {item['month'].date(): item['count'] for item in monthly_data}
    
    for i in range(12):
        month_date = current_date.replace(day=1)
        labels.append(month_date.strftime('%b %Y'))
        data.append(data_dict.get(month_date, 0))
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Document status distribution
    status_stats = docs_qs.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return JsonResponse({
        'labels': labels,
        'datasets': [{
            'label': 'Documents Uploaded',
            'data': data,
            'backgroundColor': 'rgba(13, 110, 253, 0.1)',
            'borderColor': '#0d6efd',
            'borderWidth': 2,
            'fill': True,
            'tension': 0.4
        }],
        'status_distribution': list(status_stats),
        'total_documents': docs_qs.count(),
        'active_documents': docs_qs.filter(is_archived=False).count(),
    })

# Add a simple management command to create test data for demonstration
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import Document
import random
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample documents for dashboard testing'
    
    def handle(self, *args, **options):
        # This would be a management command to create test data
        # Implementation would go here
        self.stdout.write(
            self.style.SUCCESS('Sample data creation command ready')
        )
