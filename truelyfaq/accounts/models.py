import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

# Add manager_email field to the Website model
class Website(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=64, unique=True, blank=True)
    manager_email = models.EmailField(max_length=255, blank=True, help_text="Email address for the website manager")
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = self._generate_api_key()
        super().save(*args, **kwargs)

    def _generate_api_key(self):
        return get_random_string(64)

    def __str__(self):
        return self.name
