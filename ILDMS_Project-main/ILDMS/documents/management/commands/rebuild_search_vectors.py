from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector
from main.models import Document
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Rebuild search vectors for all documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress information',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] " if dry_run else ""}Rebuilding search vectors for all documents...'
            )
        )
        
        documents = Document.objects.all()
        total_count = documents.count()
        updated_count = 0
        error_count = 0
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING('No documents found to process.'))
            return
        
        self.stdout.write(f'Found {total_count} documents to process.')
        
        for i, document in enumerate(documents, 1):
            try:
                if verbose:
                    self.stdout.write(f'Processing {i}/{total_count}: {document.title} (ID: {document.pk})')
                
                if not dry_run:
                    # Update search vector with comprehensive field coverage
                    Document.objects.filter(pk=document.pk).update(
                        search_vector=(
                            SearchVector('title', weight='A', config='english') +
                            SearchVector('content', weight='B', config='english') +
                            SearchVector('html_content', weight='B', config='english') +
                            SearchVector('description', weight='C', config='english') +
                            SearchVector('audio_transcript', weight='D', config='english')
                        )
                    )
                
                updated_count += 1
                
                # Show progress every 50 documents
                if i % 50 == 0 or i == total_count:
                    self.stdout.write(f'Progress: {i}/{total_count} ({(i/total_count)*100:.1f}%)')
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing document {document.pk} ({document.title}): {str(e)}'
                    )
                )
                
                if verbose:
                    logger.exception(f'Error updating search vector for document {document.pk}')
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[DRY RUN] Would have updated {updated_count} documents.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated search vectors for {updated_count} documents.'
                )
            )
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'{error_count} documents had errors and were skipped.'
                )
            )
        
        # Additional info
        self.stdout.write(
            self.style.SUCCESS(
                '\nSearch vector rebuild complete! You can now test the search functionality.'
            )
        )
