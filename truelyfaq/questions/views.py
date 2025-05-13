from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Question, Answer
from truelyfaq.faqs.models import FAQ
from truelyfaq.faqs.utils import check_similar_questions
import threading

# Utility function for sending emails in a background thread
def send_email_in_thread(subject, message, recipient_list, html_message=None, answer_id=None):
    """
    Send an email in a separate thread to avoid blocking the main thread.
    """
    def email_task():
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            # Update email_sent status if answer_id is provided
            if answer_id:
                Answer.objects.filter(id=answer_id).update(email_sent=True)
        except Exception as e:
            print(f"Email sending failed: {e}")
    
    # Start the email sending in a separate thread
    email_thread = threading.Thread(target=email_task)
    email_thread.daemon = True  # Thread will exit when main thread exits
    email_thread.start()

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
        
        # Create HTML message using the template
        html_message = render_to_string('emails/answer_notification.html', {
            'website_name': question.website.name,
            'question_text': question.question_text,
            'answer_text': answer_text
        })
        
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        # Send email in background thread using the utility function
        send_email_in_thread(
            subject=subject,
            message=plain_message,
            recipient_list=[question.user_email],
            html_message=html_message,
            answer_id=answer.id
        )
        
        # Mark the question as answered
        question.is_answered = True
        question.save()
        
        # Check if this should become an FAQ
        check_similar_questions(question)
        
        messages.success(request, "Question answered successfully.")
    
    return redirect('website_detail', website_id=question.website.id)
