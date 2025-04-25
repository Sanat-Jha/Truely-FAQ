from django.urls import path
from . import views

urlpatterns = [
    path('answer/<int:question_id>/', views.answer_question, name='answer_question'),
    # Add other question-related URLs here
]