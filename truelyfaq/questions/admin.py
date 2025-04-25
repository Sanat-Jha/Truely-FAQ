from django.contrib import admin
from .models import Question, Answer

class AnswerInline(admin.StackedInline):
    model = Answer
    extra = 0

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'user_email', 'website', 'is_answered', 'created_at')
    list_filter = ('is_answered', 'created_at', 'website')
    search_fields = ('question_text', 'user_email')
    inlines = [AnswerInline]

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answered_by', 'email_sent', 'created_at')
    list_filter = ('email_sent', 'created_at')
    search_fields = ('answer_text', 'question__question_text')
