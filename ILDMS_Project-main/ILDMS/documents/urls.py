from django.urls import path
from . import views
from .test_ai_search import AISearchTestView

app_name = 'documents'

urlpatterns = [
    path('', views.home, name='home'),  # handles "/"
    path('documents-list', views.DocumentListView.as_view(), name='document_list'),
    path('pending-review/', views.PendingReviewListView.as_view(), name='pending_review'),
    path('upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('create/',views.DocumentCreateView.as_view(),name='document_create'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('<int:pk>/update/', views.DocumentUpdateView.as_view(), name='document_update'),
    path('<int:pk>/edit-word/', views.DocumentWordEditView.as_view(), name='document_word_edit'),
    path('<int:pk>/download/', views.DocumentDownloadView.as_view(), name='document_download'),
    path('<int:pk>/convert-to-pdf/', views.DocumentConvertToPDFView.as_view(), name='document_convert_to_pdf'),
    path('<int:pk>/download-pdf/', views.DocumentPDFDownloadView.as_view(), name='document_pdf_download'),
    path('<int:pk>/processing-status/', views.DocumentProcessingStatusView.as_view(), name='document_processing_status'),
    path('<int:document_pk>/versions/new/', views.DocumentVersionCreateView.as_view(), name='version_create'),
    path('<int:pk>/update-content/', views.DocumentUpdateContentView.as_view(), name='document_update_content'),
    path('<int:pk>/archive/', views.DocumentArchiveView.as_view(), name='document_archive'),
    path('<int:pk>/restore/', views.DocumentRestoreView.as_view(), name='document_restore'),
    path('<int:pk>/delete-permanent/', views.DocumentPermanentDeleteView.as_view(), name='document_permanent_delete'),
    path('archived/', views.ArchivedDocumentListView.as_view(), name='archived_documents'),
    path('audit-log/', views.AuditLogListView.as_view(), name='audit_log'),
    path('audit-log/export/', views.AuditLogExportView.as_view(), name='audit_log_export'),
    path('audit-log/<int:log_id>/detail/', views.AuditLogDetailView.as_view(), name='audit_log_detail'),
    # AI Search Test Endpoint
    path('test-ai-search/', AISearchTestView.as_view(), name='test_ai_search'),
    # path('pdf-viewer/', views.PDFViewerView.as_view(), name='pdf_viewer'),
]
