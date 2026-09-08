# accounts/models.py
from django.db import models
from django.utils import timezone
from main.models import User  # Import your existing User model
from datetime import timedelta
import secrets

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Token for {self.user.email}"

    @classmethod
    def create_token(cls, user):
        token = secrets.token_hex(32)
        expires_at = timezone.now() + timedelta(days=1)
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )