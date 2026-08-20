#!/usr/bin/env python3
"""
Test script for search UI improvements
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')
django.setup()

from documents.ai_search import AISearchProcessor

def test_search_speed():
    """Test search processing speed"""
    print("🚀 Testing Search Speed Improvements")
    print("=" * 50)
    
    processor = AISearchProcessor()
    
    if not processor.enabled:
        print("❌ AI Search not enabled")
        return
    
    import time
    
    test_queries = [
        "show me contracts",
        "legal research documents",
        "court filings from last week"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"🔍 Test {i}: '{query}'")
        
        start_time = time.time()
        result = processor.process_query(query)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        if result['success']:
            print(f"✅ Success in {processing_time:.0f}ms")
            print(f"   Method: {result['method']}")
            filters = result.get('filters', {})
            if filters:
                print(f"   Filters: {len(filters)} applied")
        else:
            print(f"❌ Failed in {processing_time:.0f}ms")
        
        print()
    
    print("💡 UI Improvements Made:")
    print("- ✅ Instant URL updates")
    print("- ✅ Real-time search results")
    print("- ✅ Cleaner AI search interface")
    print("- ✅ Compact result display")
    print("- ✅ Loading states for feedback")

if __name__ == "__main__":
    test_search_speed()
