from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import JSONField
import uuid

User = get_user_model()


class SearchQuery(models.Model):
    """Model to track user search queries for analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='search_queries'
    )
    query = models.TextField(max_length=500)
    query_type = models.CharField(
        max_length=20,
        choices=[
            ('REGULAR', 'Regular Search'),
            ('AI', 'AI Search'),
            ('FILTER', 'Filter Search'),
        ],
        default='REGULAR'
    )
    results_count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['query_type', 'timestamp']),
        ]
        permissions = [
            ('can_view_analytics', 'Can view analytics dashboard'),
            ('can_export_analytics', 'Can export analytics data'),
            ('can_view_search_analytics', 'Can view search analytics'),
        ]

    def __str__(self):
        return f"Search: {self.query[:50]}... by {self.user or 'Anonymous'}"


class AnalyticsSnapshot(models.Model):
    """Daily analytics snapshots for performance optimization"""
    date = models.DateField(unique=True)
    total_documents = models.IntegerField(default=0)
    active_documents = models.IntegerField(default=0)
    archived_documents = models.IntegerField(default=0)
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    documents_uploaded_today = models.IntegerField(default=0)
    document_views_today = models.IntegerField(default=0)
    searches_today = models.IntegerField(default=0)
    
    # Document type distribution (JSON field)
    document_type_distribution = JSONField(default=dict)
    
    # Top users by activity
    top_uploaders = JSONField(default=list)
    top_viewers = JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"Analytics for {self.date}"


class UserActivity(models.Model):
    """Track user activity for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(
        max_length=30,
        choices=[
            ('LOGIN', 'User Login'),
            ('LOGOUT', 'User Logout'),
            ('DOCUMENT_UPLOAD', 'Document Upload'),
            ('DOCUMENT_VIEW', 'Document View'),
            ('DOCUMENT_DOWNLOAD', 'Document Download'),
            ('DOCUMENT_EDIT', 'Document Edit'),
            ('SEARCH', 'Search Performed'),
            ('PROFILE_UPDATE', 'Profile Update'),
        ]
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    additional_data = JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"


class SystemMetrics(models.Model):
    """Store system-wide metrics"""
    metric_name = models.CharField(max_length=100, unique=True)
    metric_value = models.TextField()  # Store as JSON string for flexibility
    description = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['metric_name']
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value[:50]}..."
