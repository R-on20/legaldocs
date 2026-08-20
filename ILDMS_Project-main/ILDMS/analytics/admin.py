from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import SearchQuery, AnalyticsSnapshot, UserActivity, SystemMetrics


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'user', 'query_type', 'results_count', 'timestamp', 'session_key')
    list_filter = ('query_type', 'timestamp', 'user')
    search_fields = ('query', 'user__username', 'user__email', 'session_key')
    readonly_fields = ('id', 'timestamp', 'session_key', 'ip_address')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Search Details', {
            'fields': ('query', 'query_type', 'results_count')
        }),
        ('User Information', {
            'fields': ('user', 'session_key', 'ip_address')
        }),
        ('Metadata', {
            'fields': ('id', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')
    
    def has_add_permission(self, request):
        return False  # Search queries are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Search queries should not be modified
    
    actions = ['delete_old_queries']
    
    def delete_old_queries(self, request, queryset):
        """Delete search queries older than 90 days"""
        cutoff_date = timezone.now() - timedelta(days=90)
        count = SearchQuery.objects.filter(timestamp__lt=cutoff_date).count()
        SearchQuery.objects.filter(timestamp__lt=cutoff_date).delete()
        self.message_user(request, f"Deleted {count} search queries older than 90 days.")
    
    delete_old_queries.short_description = "Delete queries older than 90 days"


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_documents', 'total_users', 'documents_uploaded_today', 'searches_today', 'created_at')
    list_filter = ('date', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-date',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Snapshot Date', {
            'fields': ('date', 'created_at', 'updated_at')
        }),
        ('Document Statistics', {
            'fields': ('total_documents', 'active_documents', 'archived_documents', 'documents_uploaded_today', 'document_type_distribution')
        }),
        ('User Statistics', {
            'fields': ('total_users', 'active_users', 'top_uploaders', 'top_viewers')
        }),
        ('Activity Statistics', {
            'fields': ('document_views_today', 'searches_today')
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Snapshots are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Snapshots should not be modified


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'timestamp', 'ip_address', 'additional_data_summary')
    list_filter = ('activity_type', 'timestamp', 'user')
    search_fields = ('user__username', 'user__email', 'activity_type')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp', 'user')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Activity Details', {
            'fields': ('user', 'activity_type', 'timestamp')
        }),
        ('Technical Data', {
            'fields': ('ip_address', 'user_agent', 'additional_data'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')
    
    def additional_data_summary(self, obj):
        """Display a summary of the additional_data JSON field"""
        if obj.additional_data:
            keys = list(obj.additional_data.keys())
            if len(keys) > 3:
                return f"{', '.join(keys[:3])}... ({len(keys)} items)"
            return ', '.join(keys)
        return "No additional data"
    
    additional_data_summary.short_description = "Additional Data"
    
    def has_add_permission(self, request):
        return False  # User activities are tracked automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # User activities should not be modified


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ('metric_name', 'metric_value_display', 'description', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('metric_name', 'description')
    readonly_fields = ('last_updated',)
    ordering = ('metric_name',)
    
    fieldsets = (
        ('Metric Information', {
            'fields': ('metric_name', 'description')
        }),
        ('Metric Data', {
            'fields': ('metric_value',)
        }),
        ('Timestamps', {
            'fields': ('last_updated',)
        }),
    )
    
    def metric_value_display(self, obj):
        """Display metric value with appropriate formatting"""
        try:
            # Try to parse as JSON first
            import json
            value = json.loads(obj.metric_value)
            if isinstance(value, dict):
                return f"JSON object with {len(value)} keys"
            elif isinstance(value, list):
                return f"List with {len(value)} items"
            else:
                return str(value)
        except (json.JSONDecodeError, ValueError):
            # If not JSON, display as string (truncated)
            return obj.metric_value[:50] + "..." if len(obj.metric_value) > 50 else obj.metric_value
    
    metric_value_display.short_description = "Metric Value"
    
    def has_add_permission(self, request):
        return True  # Allow manual metric addition
    
    actions = ['cleanup_old_metrics']
    
    def cleanup_old_metrics(self, request, queryset):
        """Delete system metrics older than 1 year"""
        from datetime import timedelta
        from django.utils import timezone
        cutoff_date = timezone.now() - timedelta(days=365)
        count = SystemMetrics.objects.filter(last_updated__lt=cutoff_date).count()
        SystemMetrics.objects.filter(last_updated__lt=cutoff_date).delete()
        self.message_user(request, f"Deleted {count} system metrics older than 1 year.")
    
    cleanup_old_metrics.short_description = "Delete metrics older than 1 year"


# Additional admin customizations
admin.site.site_header = "ILDMS Analytics Administration"
admin.site.site_title = "ILDMS Analytics"
admin.site.index_title = "Analytics Management"
