"""
Simple AI Search Test Script
Run this to test AI search functionality without Django management commands
"""
import os
import sys
import django

# Add the Django project to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')

# Setup Django
django.setup()

# Now we can import our AI search processor
from documents.ai_search import AISearchProcessor

def test_ai_search():
    print("🤖 AI Search Test Script")
    print("=" * 50)
    
    # Initialize processor
    processor = AISearchProcessor()
    
    print(f"AI Search Enabled: {processor.enabled}")
    print()
    
    if not processor.enabled:
        print("❌ AI search is disabled. Check your OpenAI API key configuration.")
        print("   Current settings:")
        from django.conf import settings
        print(f"   - OPENAI_API_KEY: {'Set' if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY else 'Not set'}")
        print(f"   - AI_SEARCH_ENABLED: {getattr(settings, 'AI_SEARCH_ENABLED', False)}")
        return
    
    # Test queries
    test_queries = [
        "Show me contracts uploaded last month",
        "Find confidential documents about water supply",
        "Draft legal notices from this year",
        "Documents uploaded by john",
        "Show me all contracts",
        "PDFs about water rights"
    ]
    
    print("🧪 Testing Sample Queries:")
    print("-" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        print("   " + "-" * 40)
        
        try:
            result = processor.process_query(query)
            
            print(f"   ✅ Method: {result.get('method', 'unknown')}")
            print(f"   ✅ Success: {result.get('success', False)}")
            
            filters = result.get('filters', {})
            if filters:
                print("   📋 Extracted Filters:")
                for key, value in filters.items():
                    print(f"      • {key}: {value}")
            
            keywords = result.get('keywords', [])
            if keywords:
                print(f"   🔍 Keywords: {', '.join(keywords)}")
            
            if result.get('method') == 'ai' and result.get('ai_response'):
                print("   🤖 AI Response: ✅ (Valid JSON response received)")
            elif result.get('method') == 'fallback':
                print("   ⚠️  Using fallback keyword search")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Complete!")
    print("\nNext Steps:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Visit: http://127.0.0.1:8000/documents/documents-list")
    print("3. Try searching with natural language queries")
    print("\nOr test via URL:")
    print("http://127.0.0.1:8000/documents/test-ai-search/?q=show%20me%20contracts")

if __name__ == "__main__":
    test_ai_search()
