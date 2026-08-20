from django.urls import path
from django.shortcuts import render
from . import views

app_name = 'analytics'

urlpatterns = [
    # Main analytics views
    path('', views.dashboard, name='dashboard'),
    path('search/', views.search_analytics, name='search_analytics'),
    path('users/', views.user_analytics, name='user_analytics'),
    
    # API endpoints for chart data
    path('api/chart-data/', views.chart_data, name='chart_data'),
    path('api/search-terms/', views.top_search_terms_api, name='top_search_terms_api'),
    path('api/debug/', views.debug_chart_data, name='debug_chart_data'),
    
    # Test page
    path('test-charts/', lambda request: render(request, 'analytics/test_charts.html'), name='test_charts'),
    
    # Export functionality
    path('export/', views.export_data, name='export_data'),
]
