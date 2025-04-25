from django.contrib import admin
from .models import Website

@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'owner', 'created_at')
    search_fields = ('name', 'url', 'owner__username')
    list_filter = ('created_at',)
