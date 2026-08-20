# documents/management/commands/update_search_vectors.py
from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector
from main.models import Document

class Command(BaseCommand):
    help = 'Update search vectors for all documents'

    def handle(self, *args, **options):
        Document.objects.update(
            search_vector=SearchVector('title', 'content', 'description', 'audio_transcript')
        )
        self.stdout.write(self.style.SUCCESS('Successfully updated search vectors'))