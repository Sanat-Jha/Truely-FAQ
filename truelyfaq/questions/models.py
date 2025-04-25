from django.db import models
from django.contrib.auth.models import User
from truelyfaq.accounts.models import Website

class Question(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='questions')
    user_email = models.EmailField()
    question_text = models.TextField()
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.question_text[:50]}..."

class Answer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='answer')
    answer_text = models.TextField()
    answered_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Update the is_answered field of the question
        self.question.is_answered = True
        self.question.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Answer to: {self.question.question_text[:50]}..."
