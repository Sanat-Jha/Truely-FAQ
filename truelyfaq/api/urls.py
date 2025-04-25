from django.urls import path
from . import views

urlpatterns = [
    path('questions/submit/', views.submit_question, name='api_submit_question'),
    path('faqs/', views.get_faqs, name='api_get_faqs'),
]