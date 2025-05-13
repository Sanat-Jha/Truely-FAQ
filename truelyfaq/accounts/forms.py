from django import forms
from .models import Website

class WebsiteForm(forms.ModelForm):
    class Meta:
        model = Website
        fields = ['name', 'url']  # Include all required fields except owner
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Website Name'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
        }