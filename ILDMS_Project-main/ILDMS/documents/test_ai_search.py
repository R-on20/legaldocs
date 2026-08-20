"""
Test view for AI search functionality
"""
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .ai_search import AISearchProcessor
import json

class AISearchTestView(LoginRequiredMixin, View):
    """Test endpoint for AI search functionality"""
    
    def get(self, request):
        query = request.GET.get('q', '')
        
        if not query:
            return JsonResponse({
                'error': 'No query provided',
                'usage': 'Add ?q=your-search-query to test AI search'
            })
        
        processor = AISearchProcessor()
        result = processor.process_query(query)
        
        return JsonResponse({
            'query': query,
            'ai_enabled': processor.enabled,
            'result': result,
            'method': result.get('method', 'unknown'),
            'filters_found': len(result.get('filters', {})),
            'keywords_found': len(result.get('keywords', []))
        }, indent=2)
