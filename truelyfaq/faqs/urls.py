from django.urls import path
from . import views

urlpatterns = [
    path('toggle-visibility/<int:faq_id>/', views.toggle_faq_visibility, name='toggle_faq_visibility'),
    # Add other FAQ-related URLs here
]