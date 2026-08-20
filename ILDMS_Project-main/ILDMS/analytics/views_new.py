from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum, Avg, Max, Min
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, Extract
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.urls import reverse
from datetime import datetime, timedelta
import json
import csv
import calendar
from io import StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Import your actual models
from main.models import User, Document, AuditLog
from .models import SearchQuery, AnalyticsSnapshot, UserActivity, SystemMetrics

User = get_user_model()


@login_required
def dashboard(request):
    """Main analytics dashboard view with real data"""
    
    # Date range filtering
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)  # Default to 30 days
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Document metrics from actual Document model
    total_documents = Document.objects.count()
    active_documents = Document.objects.filter(is_archived=False).count()
    archived_documents = Document.objects.filter(is_archived=True).count()
    
    # User metrics
    total_users = User.objects.count()
    active_users = User.objects.filter(
        uploaded_documents__uploaded_at__date__gte=start_date
    ).distinct().count()
    
    # Documents this week/month from actual uploads
    week_start = end_date - timedelta(days=7)
    month_start = end_date - timedelta(days=30)
    
    docs_this_week = Document.objects.filter(uploaded_at__date__gte=week_start).count()
    docs_this_month = Document.objects.filter(uploaded_at__date__gte=month_start).count()
    
    # Recent document uploads (last 7 days)
    recent_uploads = Document.objects.filter(
        uploaded_at__date__gte=week_start
    ).select_related('uploaded_by').order_by('-uploaded_at')[:10]
    
    # Most viewed documents (from audit logs)
    most_viewed_documents = AuditLog.objects.filter(
        action='VIEW',
        timestamp__date__range=[start_date, end_date]
    ).values('document_id', 'document_title').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:5]
    
    # Most active users (by document uploads)
    most_active_users = User.objects.filter(
        uploaded_documents__uploaded_at__date__range=[start_date, end_date]
    ).annotate(
        upload_count=Count('uploaded_documents')
    ).filter(upload_count__gt=0).order_by('-upload_count')[:5]
    
    # Document types distribution from actual documents
    document_types = Document.objects.values('document_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Document status distribution
    document_statuses = Document.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent activity from audit logs
    recent_activities = AuditLog.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).select_related('user').order_by('-timestamp')[:10]
    
    # Calculate growth metrics
    previous_period_start = start_date - (end_date - start_date)
    previous_period_docs = Document.objects.filter(
        uploaded_at__date__range=[previous_period_start, start_date]
    ).count()
    
    docs_growth = 0
    if previous_period_docs > 0:
        docs_growth = ((docs_this_month - previous_period_docs) / previous_period_docs) * 100
    
    context = {
        'total_documents': total_documents,
        'active_documents': active_documents,
        'archived_documents': archived_documents,
        'total_users': total_users,
        'active_users': active_users,
        'docs_this_week': docs_this_week,
        'docs_this_month': docs_this_month,
        'docs_growth': round(docs_growth, 1),
        'start_date': start_date,
        'end_date': end_date,
        'recent_uploads': recent_uploads,
        'most_viewed_documents': most_viewed_documents,
        'most_active_users': most_active_users,
        'document_types': document_types,
        'document_statuses': document_statuses,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def chart_data(request):
    """API endpoint for chart data using real database queries"""
    chart_type = request.GET.get('type', 'monthly_uploads')
    
    if chart_type == 'monthly_uploads':
        # Monthly uploads trend from actual Document model
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        
        monthly_data = Document.objects.filter(
            uploaded_at__date__range=[start_date, end_date]
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
        
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Documents Uploaded',
                'data': data,
                'backgroundColor': 'rgba(52, 152, 219, 0.1)',
                'borderColor': '#3498db',
                'borderWidth': 2,
                'fill': True
            }]
        })
    
    elif chart_type == 'document_types':
        # Document types from actual Document model
        type_data = Document.objects.values('document_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        labels = []
        data = []
        colors = [
            '#2c3e50', '#3498db', '#27ae60', '#e74c3c',
            '#f39c12', '#9b59b6', '#34495e', '#1abc9c',
            '#e67e22', '#95a5a6', '#7f8c8d', '#2c3e50'
        ]
        
        for i, item in enumerate(type_data):
            doc_type = item['document_type'] or 'Unknown'
            # Get display name for document type
            for choice in Document.DocType.choices:
                if choice[0] == doc_type:
                    doc_type = choice[1]
                    break
            labels.append(doc_type)
            data.append(item['count'])
        
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Document Types',
                'data': data,
                'backgroundColor': colors[:len(data)]
            }]
        })
    
    elif chart_type == 'documents_per_user':
        # Documents per user from actual relationships
        user_data = User.objects.annotate(
            doc_count=Count('uploaded_documents')
        ).filter(doc_count__gt=0).order_by('-doc_count')[:10]
        
        labels = []
        data = []
        
        for user in user_data:
            display_name = user.get_full_name() or user.username
            labels.append(display_name)
            data.append(user.doc_count)
        
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Documents Uploaded',
                'data': data,
                'backgroundColor': [
                    '#34495e', '#2980b9', '#229954', '#d68910', '#c0392b',
                    '#7f8c8d', '#2c3e50', '#e67e22', '#27ae60', '#8e44ad'
                ]
            }]
        })
    
    elif chart_type == 'daily_activity':
        # Daily activity from actual audit logs and document uploads
        days = int(request.GET.get('days', 7))
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days-1)
        
        # Get daily document upload counts
        daily_uploads = Document.objects.filter(
            uploaded_at__range=[start_date, end_date]
        ).annotate(
            day=TruncDate('uploaded_at')
        ).values('day').annotate(
            uploads=Count('id')
        ).order_by('day')
        
        # Get daily activity from audit logs
        daily_activities = AuditLog.objects.filter(
            timestamp__range=[start_date, end_date]
        ).annotate(
            day=TruncDate('timestamp')
        ).values('day').annotate(
            activities=Count('id')
        ).order_by('day')
        
        # Combine data
        labels = []
        upload_data = []
        activity_data = []
        
        upload_dict = {item['day']: item['uploads'] for item in daily_uploads}
        activity_dict = {item['day']: item['activities'] for item in daily_activities}
        
        for i in range(days):
            day_date = (start_date.date() + timedelta(days=i))
            if days <= 7:
                labels.append(day_date.strftime('%a %m/%d'))
            else:
                labels.append(day_date.strftime('%m/%d'))
            upload_data.append(upload_dict.get(day_date, 0))
            activity_data.append(activity_dict.get(day_date, 0))
        
        return JsonResponse({
            'labels': labels,
            'datasets': [
                {
                    'label': 'Document Uploads',
                    'data': upload_data,
                    'backgroundColor': 'rgba(52, 152, 219, 0.5)',
                    'borderColor': '#3498db',
                    'borderWidth': 2
                },
                {
                    'label': 'Total Activities',
                    'data': activity_data,
                    'backgroundColor': 'rgba(46, 204, 113, 0.5)',
                    'borderColor': '#2ecc71',
                    'borderWidth': 2
                }
            ]
        })
    
    elif chart_type == 'status_distribution':
        # Document status distribution
        status_data = Document.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        labels = []
        data = []
        colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c']
        
        for i, item in enumerate(status_data):
            status = item['status'] or 'Unknown'
            # Get display name for status
            for choice in Document.Status.choices:
                if choice[0] == status:
                    status = choice[1]
                    break
            labels.append(status)
            data.append(item['count'])
        
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Document Status',
                'data': data,
                'backgroundColor': colors[:len(data)]
            }]
        })
    
    elif chart_type == 'weekly_uploads_trend':
        # Weekly uploads trend for last 12 weeks
        end_date = timezone.now().date()
        start_date = end_date - timedelta(weeks=12)
        
        weekly_data = Document.objects.filter(
            uploaded_at__date__range=[start_date, end_date]
        ).annotate(
            week=TruncWeek('uploaded_at')
        ).values('week').annotate(
            count=Count('id')
        ).order_by('week')
        
        labels = []
        data = []
        
        for item in weekly_data:
            week_start = item['week'].date()
            labels.append(week_start.strftime('%m/%d'))
            data.append(item['count'])
        
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Weekly Uploads',
                'data': data,
                'backgroundColor': 'rgba(155, 89, 182, 0.1)',
                'borderColor': '#9b59b6',
                'borderWidth': 2,
                'fill': True
            }]
        })
    
    return JsonResponse({'error': 'Invalid chart type'}, status=400)


@login_required
def search_analytics(request):
    """Search analytics using real SearchQuery data"""
    
    # Date range filtering
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')
    
    # Get search queries in date range
    search_queries = SearchQuery.objects.filter(
        timestamp__range=[start_date, end_date]
    )
    
    # Calculate metrics
    total_searches_count = search_queries.count()
    unique_users_count = search_queries.filter(user__isnull=False).values('user').distinct().count()
    avg_results = search_queries.aggregate(avg=Avg('results_count'))['avg'] or 0
    
    # Search type distribution
    search_types = search_queries.values('query_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Top search terms analysis
    all_queries = search_queries.values_list('query', flat=True)
    word_frequency = {}
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
        'with', 'by', 'is', 'are', 'was', 'were', 'a', 'an', 'this', 
        'that', 'these', 'those', 'document', 'file'
    }
    
    for query in all_queries:
        words = query.lower().split()
        for word in words:
            word = word.strip('.,!?;:"()[]{}')
            if len(word) >= 3 and word not in stop_words:
                word_frequency[word] = word_frequency.get(word, 0) + 1
    
    top_terms = sorted(word_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Search trends over time
    daily_searches = search_queries.annotate(
        day=TruncDate('timestamp')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    context = {
        'total_searches': total_searches_count,
        'unique_users': unique_users_count,
        'avg_results': round(avg_results, 1),
        'top_search_terms': top_terms,
        'search_types': search_types,
        'daily_searches': daily_searches,
        'start_date': start_date.date(),
        'end_date': end_date.date(),
        'searches_per_user': round(total_searches_count / unique_users_count, 1) if unique_users_count > 0 else 0,
    }
    
    return render(request, 'analytics/search_analytics.html', context)


@login_required
def user_analytics(request):
    """User activity analytics with real data"""
    
    # Date range filtering
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # User activity summary with real data
    user_activities = User.objects.annotate(
        uploads=Count(
            'uploaded_documents', 
            filter=Q(uploaded_documents__uploaded_at__date__range=[start_date, end_date])
        ),
        views=Count(
            'auditlog', 
            filter=Q(auditlog__action='VIEW', auditlog__timestamp__date__range=[start_date, end_date])
        ),
        last_activity=Max('uploaded_documents__uploaded_at')
    ).order_by('-uploads', '-views')
    
    # Pagination
    paginator = Paginator(user_activities, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate metrics
    total_users_count = User.objects.count()
    active_users_count = user_activities.filter(uploads__gt=0).count()
    
    # User role distribution
    user_roles = User.objects.values('role').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Top uploaders
    top_uploaders = User.objects.annotate(
        total_uploads=Count('uploaded_documents')
    ).filter(total_uploads__gt=0).order_by('-total_uploads')[:10]
    
    context = {
        'user_activities': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'total_users': total_users_count,
        'active_users_count': active_users_count,
        'user_roles': user_roles,
        'top_uploaders': top_uploaders,
        'engagement_rate': round((active_users_count * 100) / total_users_count, 1) if total_users_count > 0 else 0,
    }
    
    return render(request, 'analytics/user_analytics.html', context)


@login_required
def export_data(request):
    """Export real analytics data as CSV or PDF"""
    
    export_format = request.GET.get('format', 'csv')
    data_type = request.GET.get('type', 'documents')
    
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_{data_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        if data_type == 'documents':
            writer.writerow(['Title', 'Type', 'Status', 'Uploaded By', 'Upload Date', 'File Size'])
            
            documents = Document.objects.select_related('uploaded_by').all()
            for doc in documents:
                writer.writerow([
                    doc.title,
                    doc.get_document_type_display(),
                    doc.get_status_display(),
                    doc.uploaded_by.get_full_name() or doc.uploaded_by.username,
                    doc.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                    doc.get_file_size_display()
                ])
        
        elif data_type == 'users':
            writer.writerow(['Username', 'Full Name', 'Role', 'Email', 'Join Date', 'Documents Uploaded'])
            
            users = User.objects.annotate(doc_count=Count('uploaded_documents'))
            for user in users:
                writer.writerow([
                    user.username,
                    user.get_full_name(),
                    user.get_role_display(),
                    user.email,
                    user.date_joined.strftime('%Y-%m-%d'),
                    user.doc_count
                ])
        
        elif data_type == 'activities':
            writer.writerow(['User', 'Action', 'Document', 'Timestamp', 'IP Address'])
            
            activities = AuditLog.objects.select_related('user').all()[:1000]  # Limit to recent 1000
            for activity in activities:
                writer.writerow([
                    activity.user.username if activity.user else 'Anonymous',
                    activity.get_action_display(),
                    activity.document_title or f'ID: {activity.document_id}',
                    activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    activity.ip_address or 'Unknown'
                ])
        
        return response
    
    elif export_format == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="analytics_{data_type}_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        
        # Add title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, f"ILDMS Analytics Report - {data_type.title()}")
        
        # Add generated date
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 70, f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Add real statistics
        y_position = height - 120
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_position, "Summary Statistics:")
        
        y_position -= 30
        p.setFont("Helvetica", 10)
        
        total_docs = Document.objects.count()
        active_docs = Document.objects.filter(is_archived=False).count()
        total_users = User.objects.count()
        recent_uploads = Document.objects.filter(
            uploaded_at__date__gte=timezone.now().date() - timedelta(days=7)
        ).count()
        
        p.drawString(70, y_position, f"Total Documents: {total_docs}")
        y_position -= 20
        p.drawString(70, y_position, f"Active Documents: {active_docs}")
        y_position -= 20
        p.drawString(70, y_position, f"Archived Documents: {total_docs - active_docs}")
        y_position -= 20
        p.drawString(70, y_position, f"Total Users: {total_users}")
        y_position -= 20
        p.drawString(70, y_position, f"Uploads This Week: {recent_uploads}")
        
        p.save()
        return response
    
    return JsonResponse({'error': 'Invalid export format'}, status=400)


# Helper function to track search queries
def track_search_query(user, query, query_type='REGULAR', results_count=0, request=None):
    """Helper function to track search queries for analytics"""
    
    search_query = SearchQuery.objects.create(
        user=user if user and user.is_authenticated else None,
        query=query,
        query_type=query_type,
        results_count=results_count,
        session_key=request.session.session_key if request and hasattr(request, 'session') else '',
        ip_address=get_client_ip(request) if request else None
    )
    
    return search_query


def get_client_ip(request):
    """Get client IP address from request"""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
