from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Document, DocumentVersion, Tag, AuditLog


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role',
                    'is_verified', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_verified', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'bar_number')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Legal info'), {'fields': ('role', 'bar_number', 'specialization')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified',
                       'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'last_updated')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2',
                       'role', 'phone', 'bar_number', 'is_staff', 'is_active'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('groups')

    def get_fieldsets(self, request, obj=None):
        if not obj:  # This is the add form
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'uploaded_by', 'uploaded_at', 'confidential')
    list_filter = ('document_type', 'tags', 'confidential')
    search_fields = ('title', 'content', 'uploaded_by__username')
    list_select_related = ('uploaded_by',)
    raw_id_fields = ('uploaded_by',)
    filter_horizontal = ('tags',)
    date_hierarchy = 'uploaded_at'

    fieldsets = (
        (None, {'fields': ('title', 'document_type', 'file')}),
        (_('Metadata'), {'fields': ('uploaded_by', 'description', 'tags', 'confidential')}),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'version_number', 'created_at', 'created_by')
    list_filter = ('created_at',)
    raw_id_fields = ('document', 'created_by')


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by')
    search_fields = ('name',)
    raw_id_fields = ('created_by',)


from django.utils.html import format_html
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'user_display',
        'action_display',
        'document_display',
        'additional_info_preview'
    )
    list_filter = ('action', 'timestamp')
    search_fields = (
        'document_title',
        'document_id',
        'user__username',
        'user__email'
    )
    readonly_fields = ('timestamp', 'action', 'document_id', 'document_title')
    date_hierarchy = 'timestamp'
    list_per_page = 50

    def user_display(self, obj):
        return obj.user.get_full_name() if obj.user else "System"
    user_display.short_description = 'User'

    def action_display(self, obj):
        colors = {
            'CREATE': 'green',
            'UPDATE': 'blue',
            'ARCHIVE': 'orange',
            'RESTORE': 'teal',
            'DELETE': 'red'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.action, 'black'),
            obj.get_action_display()
        )
    action_display.short_description = 'Action'

    def document_display(self, obj):
        return f"{obj.document_title} (ID: {obj.document_id})"
    document_display.short_description = 'Document'

    def additional_info_preview(self, obj):
        return str(obj.additional_info)[:50] + '...' if obj.additional_info else ''
    additional_info_preview.short_description = 'Details'

    def has_add_permission(self, request):
        return False  # Prevent adding logs manually through admin

admin.site.register(User, CustomUserAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(DocumentVersion, DocumentVersionAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(AuditLog, AuditLogAdmin)