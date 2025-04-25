from django.db import models
from truelyfaq.accounts.models import Website

class FAQ(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='faqs')
    question_text = models.TextField()
    answer_text = models.TextField()
    similarity_count = models.IntegerField(default=1)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-similarity_count']

    def __str__(self):
        return f"{self.question_text[:50]}..."
