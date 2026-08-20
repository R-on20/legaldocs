#!/usr/bin/env python3
"""
Test script for debugging AI search improvements
Tests the corrected document type mapping and separate search forms
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')
django.setup()

from documents.ai_search import AISearchProcessor
from main.models import Document

def test_ai_search_improvements():
    """Test the AI search improvements"""
    print("🧪 Testing AI Search Improvements")
    print("=" * 50)
    
    # Initialize AI processor
    processor = AISearchProcessor()
    
    if not processor.enabled:
        print("❌ AI Search not enabled - check OpenAI configuration")
        return
    
    # Test queries that were problematic
    test_queries = [
        "show me all Legal Research documents",
        "find court filings from last month",
        "legal research about water rights",
        "contracts uploaded by john",
        "confidential documents"
    ]
    
    print(f"🤖 AI Processor Status: {'✅ Enabled' if processor.enabled else '❌ Disabled'}")
    print()
    
    # Show available document types
    print("📋 Available Document Types:")
    for choice in Document.DocType.choices:
        print(f"  - {choice[0]}: {choice[1]}")
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"🔍 Test {i}: '{query}'")
        print("-" * 40)
        
        try:
            result = processor.process_query(query)
            
            if result['success']:
                print(f"✅ Success! Method: {result['method']}")
                print(f"📊 Extracted Filters:")
                
                filters = result.get('filters', {})
                if filters:
                    for key, value in filters.items():
                        print(f"   {key}: {value}")
                else:
                    print("   No specific filters extracted")
                
                keywords = result.get('keywords', [])
                if keywords:
                    print(f"🔑 Keywords: {keywords}")
                
                # Check document type mapping specifically
                doc_type = filters.get('document_type')
                if doc_type:
                    # Verify it's a valid document type
                    valid_types = [choice[0] for choice in Document.DocType.choices]
                    if doc_type in valid_types:
                        print(f"✅ Document type mapping: {doc_type} (Valid)")
                    else:
                        print(f"❌ Document type mapping: {doc_type} (Invalid)")
                
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print()
    
    print("🧪 Testing document type mapping specifically...")
    print("-" * 50)
    
    # Test specific document type mapping
    mapping_tests = [
        ("legal research documents", "RESEARCH"),
        ("court filing documents", "COURT_FILING"), 
        ("case law and judgments", "CASE_LAW"),
        ("contracts and agreements", "CONTRACT"),
        ("legal notices", "LEGAL_NOTICE"),
        ("practice notes", "PRACTICE_NOTE")
    ]
    
    for query, expected_type in mapping_tests:
        result = processor.process_query(query)
        if result['success']:
            actual_type = result.get('filters', {}).get('document_type')
            status = "✅" if actual_type == expected_type else "❌"
            print(f"{status} '{query}' → Expected: {expected_type}, Got: {actual_type}")
        else:
            print(f"❌ '{query}' → Failed to process")

if __name__ == "__main__":
    test_ai_search_improvements()
