import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

class Website(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='websites')
    name = models.CharField(max_length=255)
    url = models.URLField()
    api_key = models.CharField(max_length=64, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = self._generate_api_key()
        super().save(*args, **kwargs)

    def _generate_api_key(self):
        return get_random_string(64)

    def __str__(self):
        return self.name
