from django.urls import path
from . import views
from ..faqs.views import create_faq_manually

urlpatterns = [
    path('answer/<int:question_id>/', views.answer_question, name='answer_question'),
    path('<int:question_id>/create-faq/', create_faq_manually, name='create_faq_manually'),
    # Add other question-related URLs here
]