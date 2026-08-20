"""
Management command to test AI search functionality
"""
from django.core.management.base import BaseCommand
from documents.ai_search import AISearchProcessor
import json

class Command(BaseCommand):
    help = 'Test AI search functionality with sample queries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--query',
            type=str,
            help='Custom query to test',
        )
        parser.add_argument(
            '--run-samples',
            action='store_true',
            help='Run sample queries',
        )
    
    def handle(self, *args, **options):
        processor = AISearchProcessor()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"AI Search Enabled: {processor.enabled}"
            )
        )
        
        if not processor.enabled:
            self.stdout.write(
                self.style.WARNING(
                    "AI search is disabled. Check your OpenAI API key configuration."
                )
            )
            return
        
        if options['query']:
            self.test_query(processor, options['query'])
        
        if options['run_samples']:
            self.run_sample_queries(processor)
        
        if not options['query'] and not options['run_samples']:
            self.stdout.write(
                self.style.WARNING(
                    "No query specified. Use --query 'your query' or --run-samples"
                )
            )
    
    def test_query(self, processor, query):
        self.stdout.write(f"\nTesting query: '{query}'")
        self.stdout.write("-" * 50)
        
        result = processor.process_query(query)
        
        self.stdout.write(f"Method: {result.get('method', 'unknown')}")
        self.stdout.write(f"Success: {result.get('success', False)}")
        
        filters = result.get('filters', {})
        if filters:
            self.stdout.write("Extracted Filters:")
            for key, value in filters.items():
                self.stdout.write(f"  {key}: {value}")
        
        keywords = result.get('keywords', [])
        if keywords:
            self.stdout.write(f"Keywords: {', '.join(keywords)}")
        
        if result.get('ai_response'):
            self.stdout.write("AI Response:")
            try:
                ai_data = json.loads(result['ai_response'])
                self.stdout.write(json.dumps(ai_data, indent=2))
            except:
                self.stdout.write(result['ai_response'])
    
    def run_sample_queries(self, processor):
        sample_queries = [
            "Show me contracts uploaded last month",
            "Find confidential documents about water supply",
            "Draft legal notices from this year",
            "Documents uploaded by john",
            "Approved agreements about service contracts",
            "Show me all PDFs",
            "Contracts from last week",
            "Find court filings",
            "Water rights agreements",
            "Documents uploaded yesterday"
        ]
        
        self.stdout.write("\nRunning sample queries...")
        self.stdout.write("=" * 60)
        
        for query in sample_queries:
            self.test_query(processor, query)
            self.stdout.write()
