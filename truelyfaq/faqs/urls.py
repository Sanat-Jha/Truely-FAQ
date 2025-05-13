from django.urls import path
from . import views

urlpatterns = [
    path('toggle-visibility/<int:faq_id>/', views.toggle_faq_visibility, name='toggle_faq_visibility'),
path('website/<int:website_id>/find-similar-questions/', views.find_similar_questions, name='find_similar_questions'),
]