import threading
from django.core.mail import send_mail
from django.conf import settings

def send_email_in_thread(subject, message, recipient_list, html_message=None):
    """
    Send an email in a separate thread to avoid blocking the main thread.
    """
    def email_task():
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
    
    # Start the email sending in a separate thread
    email_thread = threading.Thread(target=email_task)
    email_thread.daemon = True  # Thread will exit when main thread exits
    email_thread.start()