from django.contrib import admin
from .models import FAQ

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'website', 'similarity_count', 'is_visible', 'created_at')
    list_filter = ('is_visible', 'created_at', 'website')
    search_fields = ('question_text', 'answer_text')
