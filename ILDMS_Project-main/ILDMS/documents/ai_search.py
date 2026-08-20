"""
AI-powered natural language search for legal documents using OpenAI
"""
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from main.models import Document

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Natural language search will fall back to keyword search.")


class AISearchProcessor:
    """
    Processes natural language queries using OpenAI to extract search filters
    """
    
    def __init__(self):
        if OPENAI_AVAILABLE and hasattr(settings, 'OPENAI_API_KEY'):
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.enabled = True
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.enabled = False
        else:
            self.enabled = False
            logger.warning("OpenAI API key not configured. AI search disabled.")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query and extract search filters
        
        Args:
            query: Natural language search query
            
        Returns:
            Dictionary with extracted filters and metadata
        """
        if not self.enabled:
            return self._fallback_processing(query)
        
        try:
            # Get AI-powered analysis
            ai_response = self._call_openai_api(query)
            filters = self._parse_ai_response(ai_response)
            
            # Validate and clean filters
            validated_filters = self._validate_filters(filters)
            
            return {
                'success': True,
                'method': 'ai',
                'filters': validated_filters,
                'keywords': filters.get('keywords', []),
                'original_query': query,
                'ai_response': ai_response
            }
            
        except Exception as e:
            logger.error(f"AI search processing failed: {e}")
            return self._fallback_processing(query)
    
    def _call_openai_api(self, query: str) -> str:
        """Call OpenAI API with structured prompt"""
        
        # Define available document types with better mapping
        doc_types_mapping = {
            'CONSTITUTION': 'Constitution',
            'BILL': 'Bill',
            'ACT': 'Act of Parliament',
            'LEGAL_NOTICE': 'Legal Notice',
            'PRACTICE_NOTE': 'Practice Note', 
            'TREATY': 'Treaty',
            'CASE_LAW': 'Case Law, Judgment',
            'CONTRACT': 'Contract, Agreement',
            'COURT_FILING': 'Court Filing',
            'CORRESPONDENCE': 'Correspondence, Letter',
            'RESEARCH': 'Legal Research, Research Document',
            'AUDIO': 'Audio Recording',
            'VIDEO': 'Video Recording',
            'OTHER': 'Other Document'
        }
        
        doc_statuses = [choice[0] for choice in Document.Status.choices]
        
        # Create a more detailed mapping for the AI
        doc_types_prompt = []
        for code, description in doc_types_mapping.items():
            doc_types_prompt.append(f'"{code}": {description}')
        
        prompt = f"""
You are an AI assistant helping to parse legal document search queries. 
Extract search criteria from the user's natural language query and return them as JSON.

Available document types and their meanings:
{', '.join(doc_types_prompt)}

Important mapping rules:
- "Legal Research" or "Research" → "RESEARCH"  
- "Court Filing" or "Filing" → "COURT_FILING"
- "Case Law" or "Judgment" → "CASE_LAW"
- "Contract" or "Agreement" → "CONTRACT"
- "Legal Notice" → "LEGAL_NOTICE"
- "Practice Note" → "PRACTICE_NOTE"

Available statuses: {', '.join(doc_statuses)}

User query: "{query}"

Extract the following information and return as valid JSON:
{{
    "document_type": "exact match from available types or null",
    "status": "exact match from available statuses or null", 
    "confidential": true/false/null,
    "date_range": {{
        "start_date": "YYYY-MM-DD or null",
        "end_date": "YYYY-MM-DD or null",
        "relative": "last_week/last_month/last_year/this_week/this_month/this_year or null"
    }},
    "keywords": ["array", "of", "relevant", "keywords"],
    "uploaded_by": "username if mentioned or null",
    "title_contains": "specific title terms or null",
    "content_contains": "specific content terms or null"
}}

Examples:
- "contracts from last month" → {{"document_type": "CONTRACT", "date_range": {{"relative": "last_month"}}, "keywords": ["contracts"]}}
- "confidential PDFs uploaded by john" → {{"confidential": true, "uploaded_by": "john", "keywords": ["pdf"]}}
- "legal research documents" → {{"document_type": "RESEARCH", "keywords": ["legal", "research"]}}
- "court filings" → {{"document_type": "COURT_FILING", "keywords": ["court", "filings"]}}
- "water supply agreements" → {{"keywords": ["water", "supply", "agreements"]}}

Return only valid JSON, no explanations.
"""
        
        response = self.client.chat.completions.create(
            model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts search criteria from legal document queries. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1  # Low temperature for consistent parsing
        )
        
        return response.choices[0].message.content.strip()
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse the AI response JSON"""
        try:
            # Clean up the response (remove any markdown formatting)
            cleaned_response = re.sub(r'```json\s*|\s*```', '', ai_response)
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"AI response was: {ai_response}")
            raise
    
    def _validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the extracted filters"""
        validated = {}
        
        # Validate document type
        if filters.get('document_type'):
            doc_type = filters['document_type'].upper()
            valid_types = [choice[0] for choice in Document.DocType.choices]
            if doc_type in valid_types:
                validated['document_type'] = doc_type
        
        # Validate status
        if filters.get('status'):
            status = filters['status'].upper()
            valid_statuses = [choice[0] for choice in Document.Status.choices]
            if status in valid_statuses:
                validated['status'] = status
        
        # Validate confidential flag
        if isinstance(filters.get('confidential'), bool):
            validated['confidential'] = filters['confidential']
        
        # Process date range
        date_range = filters.get('date_range', {})
        if date_range:
            processed_dates = self._process_date_range(date_range)
            if processed_dates:
                validated.update(processed_dates)
        
        # Clean keywords
        keywords = filters.get('keywords', [])
        if keywords and isinstance(keywords, list):
            validated['keywords'] = [kw.strip() for kw in keywords if kw.strip()]
        
        # Other fields
        for field in ['uploaded_by', 'title_contains', 'content_contains']:
            if filters.get(field):
                validated[field] = filters[field].strip()
        
        return validated
    
    def _process_date_range(self, date_range: Dict[str, Any]) -> Dict[str, Any]:
        """Process date range filters"""
        result = {}
        
        # Handle relative dates
        relative = date_range.get('relative')
        if relative:
            now = timezone.now()
            
            if relative == 'last_week':
                start_date = now - timedelta(weeks=1)
                result['uploaded_after'] = start_date.date()
            elif relative == 'last_month':
                start_date = now - timedelta(days=30)
                result['uploaded_after'] = start_date.date()
            elif relative == 'last_year':
                start_date = now - timedelta(days=365)
                result['uploaded_after'] = start_date.date()
            elif relative == 'this_week':
                start_date = now - timedelta(days=now.weekday())
                result['uploaded_after'] = start_date.date()
            elif relative == 'this_month':
                start_date = now.replace(day=1)
                result['uploaded_after'] = start_date.date()
            elif relative == 'this_year':
                start_date = now.replace(month=1, day=1)
                result['uploaded_after'] = start_date.date()
        
        # Handle explicit dates
        start_date = date_range.get('start_date')
        end_date = date_range.get('end_date')
        
        if start_date:
            try:
                result['uploaded_after'] = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if end_date:
            try:
                result['uploaded_before'] = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        return result
    
    def _fallback_processing(self, query: str) -> Dict[str, Any]:
        """Fallback to keyword-based search when AI is unavailable"""
        keywords = self._extract_keywords(query)
        
        return {
            'success': True,
            'method': 'fallback',
            'filters': {},
            'keywords': keywords,
            'original_query': query,
            'ai_response': None
        }
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Simple keyword extraction for fallback"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'show', 'me',
            'find', 'search', 'get', 'all', 'documents', 'files'
        }
        
        # Simple word extraction
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Limit to 10 keywords


def apply_ai_filters_to_queryset(queryset, ai_result: Dict[str, Any]):
    """
    Apply AI-extracted filters to a Django queryset
    
    Args:
        queryset: Django QuerySet for Document model
        ai_result: Result from AISearchProcessor.process_query()
        
    Returns:
        Filtered QuerySet
    """
    filters = ai_result.get('filters', {})
    
    # Apply basic filters
    if 'document_type' in filters:
        queryset = queryset.filter(document_type=filters['document_type'])
    
    if 'status' in filters:
        queryset = queryset.filter(status=filters['status'])
    
    if 'confidential' in filters:
        queryset = queryset.filter(confidential=filters['confidential'])
    
    # Apply date filters
    if 'uploaded_after' in filters:
        queryset = queryset.filter(uploaded_at__gte=filters['uploaded_after'])
    
    if 'uploaded_before' in filters:
        queryset = queryset.filter(uploaded_at__lte=filters['uploaded_before'])
    
    # Apply user filter
    if 'uploaded_by' in filters:
        queryset = queryset.filter(uploaded_by__username__icontains=filters['uploaded_by'])
    
    # Apply title filter
    if 'title_contains' in filters:
        queryset = queryset.filter(title__icontains=filters['title_contains'])
    
    # Apply content filter
    if 'content_contains' in filters:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(content__icontains=filters['content_contains']) |
            Q(html_content__icontains=filters['content_contains']) |
            Q(audio_transcript__icontains=filters['content_contains'])
        )
    
    # Apply keyword search if no other filters matched
    keywords = ai_result.get('keywords', [])
    if keywords and not any(key in filters for key in ['title_contains', 'content_contains']):
        from documents.utils import get_search_queryset
        keyword_query = ' '.join(keywords)
        queryset = get_search_queryset(queryset, keyword_query)
    
    return queryset
