from rest_framework import permissions
from truelyfaq.accounts.models import Website

class IsWebsiteOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a website to access its data.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the website
        if hasattr(obj, 'website'):
            return obj.website.owner == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False

class HasValidAPIKey(permissions.BasePermission):
    """
    Custom permission to only allow access to clients with valid API key.
    """
    def has_permission(self, request, view):
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            return False
        
        # Check if the API key exists
        return Website.objects.filter(api_key=api_key).exists()