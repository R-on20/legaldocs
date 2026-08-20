from django.contrib.postgres.search import (
    SearchQuery, SearchRank, SearchVector, SearchHeadline
)
from django.db.models import Q
import re
import logging

logger = logging.getLogger(__name__)

def get_search_queryset(queryset, search_query):
    """
    Comprehensive search across multiple fields with fallback mechanisms
    """
    if not search_query or not search_query.strip():
        return queryset.none()

    search_query = search_query.strip()
    logger.info(f"Performing search for: '{search_query}'")
    
    # Extract search terms for fallback search
    search_terms = extract_search_terms(search_query)
    logger.info(f"Extracted search terms: {search_terms}")
    
    # Try PostgreSQL full-text search first
    try:
        logger.info("Attempting PostgreSQL full-text search")
        
        # Create search query object with better configuration
        query = SearchQuery(search_query, config='english', search_type='websearch')
        
        # Create comprehensive search vector including html_content
        vector = (
            SearchVector('title', weight='A', config='english') +
            SearchVector('content', weight='B', config='english') +
            SearchVector('html_content', weight='B', config='english') +
            SearchVector('description', weight='C', config='english') +
            SearchVector('audio_transcript', weight='D', config='english')
        )
        
        # Perform search with annotations
        search_results = queryset.annotate(
            search=vector,
            rank=SearchRank(vector, query),
            title_headline=SearchHeadline(
                'title',
                query,
                config='english',
                start_sel='<mark>',
                stop_sel='</mark>'
            ),
            content_headline=SearchHeadline(
                'content',
                query,
                config='english',
                start_sel='<mark>',
                stop_sel='</mark>',
                max_fragments=3,
                fragment_delimiter=" [...] "
            ),
            transcript_headline=SearchHeadline(
                'audio_transcript',
                query,
                config='english',
                start_sel='<mark class="transcript">',
                stop_sel='</mark>',
                max_fragments=2
            )
        ).filter(search=query).order_by('-rank')
        
        search_count = search_results.count()
        logger.info(f"PostgreSQL search found {search_count} results")
        
        if search_count > 0:
            return search_results
        else:
            logger.info("PostgreSQL search returned no results, trying fallback")
            
    except Exception as e:
        logger.warning(f"PostgreSQL full-text search failed: {e}")
    
    # Fallback to Django ORM search with comprehensive field coverage
    logger.info("Using fallback ORM search")
    return _fallback_search(queryset, search_terms)

def _fallback_search(queryset, search_terms):
    """
    Fallback search using Django ORM with comprehensive field coverage
    """
    if not search_terms:
        return queryset.none()
    
    # Build Q objects for each term across all searchable fields
    final_q = Q()
    
    for term in search_terms:
        if not term.strip():
            continue
            
        term = term.strip()
        logger.info(f"Building fallback search for term: '{term}'")
        
        # Create Q object for this term across all relevant fields
        term_q = (
            Q(title__icontains=term) |
            Q(content__icontains=term) |
            Q(html_content__icontains=term) |
            Q(description__icontains=term) |
            Q(audio_transcript__icontains=term)
        )
        
        # For phrases (multi-word terms), use AND logic
        # For single words, use OR logic
        if len(search_terms) == 1 or ' ' in term:
            final_q = term_q if not final_q else (final_q & term_q)
        else:
            final_q = term_q if not final_q else (final_q | term_q)
    
    results = queryset.filter(final_q).distinct()
    result_count = results.count()
    logger.info(f"Fallback search found {result_count} results")
    
    return results

def extract_search_terms(search_query):
    """
    Extract individual search terms from a search query,
    handling quoted phrases and individual words.
    """
    if not search_query:
        return []
    
    # Handle quoted phrases and individual words
    terms = []
    
    # Find quoted phrases first
    quoted_pattern = r'"([^"]*)"'
    quoted_matches = re.findall(quoted_pattern, search_query)
    
    # Remove quoted phrases from query to avoid double-matching
    clean_query = re.sub(quoted_pattern, '', search_query)
    
    # Add quoted phrases as single terms
    terms.extend([phrase.strip() for phrase in quoted_matches if phrase.strip()])
    
    # Add individual words from remaining query
    words = clean_query.split()
    terms.extend([word.strip() for word in words if word.strip() and len(word.strip()) > 1])
    
    return terms

def debug_search_content(document, search_terms):
    """
    Debug function to check if search terms exist in document fields
    """
    logger.info(f"Debug search for document {document.pk}: {document.title}")
    
    for term in search_terms:
        term_lower = term.lower()
        logger.info(f"Checking term '{term}':")
        logger.info(f"  - In title: {'YES' if term_lower in (document.title or '').lower() else 'NO'}")
        logger.info(f"  - In content: {'YES' if term_lower in (document.content or '').lower() else 'NO'}")
        logger.info(f"  - In html_content: {'YES' if term_lower in (document.html_content or '').lower() else 'NO'}")
        logger.info(f"  - In description: {'YES' if term_lower in (document.description or '').lower() else 'NO'}")
        logger.info(f"  - In audio_transcript: {'YES' if term_lower in (document.audio_transcript or '').lower() else 'NO'}")

def rebuild_search_vectors():
    """
    Utility function to rebuild search vectors for all documents
    """
    from main.models import Document
    
    logger.info("Rebuilding search vectors for all documents")
    
    documents = Document.objects.all()
    updated_count = 0
    
    for doc in documents:
        try:
            doc.update_search_vector()
            updated_count += 1
        except Exception as e:
            logger.error(f"Failed to update search vector for document {doc.pk}: {e}")
    
    logger.info(f"Updated search vectors for {updated_count} documents")
    return updated_count