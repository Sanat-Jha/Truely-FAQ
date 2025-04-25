from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone  # Add this import
from django.core.mail import send_mail
from django.conf import settings
from .models import Question, Answer
from truelyfaq.faqs.models import FAQ
from truelyfaq.faqs.utils import check_similar_questions
import threading

def send_answer_email(subject, message, recipient, answer_id):
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [recipient],
            fail_silently=False,
        )
        # Update email_sent status
        Answer.objects.filter(id=answer_id).update(email_sent=True)
    except Exception as e:
        print(f"Email sending failed: {e}")

@login_required
def answer_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    
    # Check if the user owns the website
    if question.website.owner != request.user:
        messages.error(request, "You don't have permission to answer this question.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        answer_text = request.POST.get('answer_text', '').strip()
        
        if not answer_text:
            messages.error(request, "Answer text cannot be empty.")
            return redirect('website_detail', website_id=question.website.id)
        
        # Create the answer
        answer = Answer.objects.create(
            question=question,
            answer_text=answer_text
        )
        
        # Prepare email content
        subject = f'Your question has been answered - {question.website.name}'
        message = f"""
Hello,

Your question: "{question.question_text}"

Has been answered: "{answer_text}"

Thank you for using our service!
{question.website.name} Team
        """
        
        # Start email sending in a separate thread
        email_thread = threading.Thread(
            target=send_answer_email,
            args=(subject, message, question.user_email, answer.id)
        )
        email_thread.start()
        
        # Mark the question as answered
        question.is_answered = True
        question.save()
        
        # Check if this should become an FAQ
        check_similar_questions(question)
        
        messages.success(request, "Question answered successfully.")
    
    return redirect('website_detail', website_id=question.website.id)
