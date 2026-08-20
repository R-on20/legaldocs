"""
Detailed AI Search Diagnostic Script
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')
django.setup()

from documents.ai_search import AISearchProcessor
from django.conf import settings

def diagnose_ai_search():
    print("🔍 AI Search Diagnostic Tool")
    print("=" * 50)
    
    # Check settings
    print("📋 Configuration Check:")
    print(f"   • OPENAI_API_KEY: {'✅ Set' if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY else '❌ Not set'}")
    print(f"   • AI_SEARCH_ENABLED: {'✅' if getattr(settings, 'AI_SEARCH_ENABLED', False) else '❌'} {getattr(settings, 'AI_SEARCH_ENABLED', False)}")
    print(f"   • OPENAI_MODEL: {getattr(settings, 'OPENAI_MODEL', 'Not set')}")
    
    # Check OpenAI library
    try:
        import openai
        print(f"   • OpenAI Library: ✅ Installed (version: {openai.__version__})")
    except ImportError:
        print("   • OpenAI Library: ❌ Not installed")
        return
    
    print()
    
    # Test processor initialization
    print("🤖 Processor Initialization:")
    try:
        processor = AISearchProcessor()
        print(f"   • Processor Enabled: {'✅' if processor.enabled else '❌'} {processor.enabled}")
        
        if hasattr(processor, 'client'):
            print("   • OpenAI Client: ✅ Initialized")
        else:
            print("   • OpenAI Client: ❌ Not initialized")
            
    except Exception as e:
        print(f"   • Error: ❌ {e}")
        return
    
    print()
    
    # Test a simple query
    if processor.enabled:
        print("🧪 Testing Simple Query:")
        test_query = "show me contracts"
        print(f"   Query: '{test_query}'")
        
        try:
            result = processor.process_query(test_query)
            print(f"   • Success: {'✅' if result.get('success') else '❌'} {result.get('success')}")
            print(f"   • Method: {result.get('method', 'unknown')}")
            
            if result.get('method') == 'ai':
                print("   • AI Processing: ✅ Working!")
                filters = result.get('filters', {})
                if filters:
                    print("   • Filters extracted:")
                    for key, value in filters.items():
                        print(f"     - {key}: {value}")
            elif result.get('method') == 'fallback':
                print("   • AI Processing: ⚠️ Fell back to keyword search")
                print("   • This could be due to:")
                print("     - API rate limits")
                print("     - Network issues")
                print("     - Invalid API key")
                print("     - Insufficient OpenAI credits")
            
            keywords = result.get('keywords', [])
            if keywords:
                print(f"   • Keywords: {', '.join(keywords)}")
                
        except Exception as e:
            print(f"   • Error: ❌ {e}")
    
    print()
    print("🎯 Next Steps:")
    if not processor.enabled:
        print("1. ❌ Fix the processor initialization issue above")
        print("2. Check your OpenAI API key")
        print("3. Ensure you have OpenAI credits")
    else:
        print("1. ✅ Try the web interface: python manage.py runserver")
        print("2. ✅ Visit: http://127.0.0.1:8000/documents/test-ai-search/?q=show%20me%20contracts")
        print("3. ✅ Or use the document list search box")
    
    print("\n💡 Manual Test Commands:")
    print("   python manage.py test_ai_search --query 'show me contracts'")
    print("   python manage.py test_ai_search --run-samples")

if __name__ == "__main__":
    diagnose_ai_search()
