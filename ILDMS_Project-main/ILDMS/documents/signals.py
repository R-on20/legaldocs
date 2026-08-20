# documents/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector
from main.models import Document

@receiver(post_save, sender=Document)
def update_document_search_vector(sender, instance, **kwargs):
    Document.objects.filter(pk=instance.pk).update(
        search_vector=SearchVector('title', 'content', 'description', 'audio_transcript')
    )