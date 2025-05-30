from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from truelyfaq.accounts.models import Website
from truelyfaq.questions.models import Question, Answer
from truelyfaq.faqs.models import FAQ
from .serializers import (
    WebsiteSerializer,
    QuestionSerializer,
    QuestionCreateSerializer,
    AnswerCreateSerializer,
    FAQSerializer,
    FAQVisibilitySerializer,
)
from .permissions import IsWebsiteOwner, HasValidAPIKey
from truelyfaq.questions.views import send_email_in_thread

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_question(request):
    """
    Submit a question via API
    """
    api_key = request.headers.get('X-Api-Key')
    if not api_key:
        return Response(
            {"error": "API key is required"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        website = Website.objects.get(api_key=api_key)
    except Website.DoesNotExist:
        return Response(
            {"error": "Invalid API key"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = QuestionCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Add website to validated data
        serializer.validated_data['website'] = website
        question = serializer.save()
        
        # Send email notification to the website manager if email is provided
        if website.manager_email:
            subject = f"New Question from {website.name}"
            
            # Create HTML message
            html_message = render_to_string('emails/new_question.html', {
                'website_name': website.name,
                'question_text': question.question_text,
                'user_email': question.user_email,
                'dashboard_url': f"{request.build_absolute_uri('/accounts/dashboard/')}"
            })
            
            # Plain text version
            plain_message = strip_tags(html_message)
            
            # Send email in background thread
            send_email_in_thread(
                subject=subject,
                message=plain_message,
                recipient_list=[website.manager_email],
                html_message=html_message
            )
        
        return Response(
            QuestionSerializer(question).data, 
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_faqs(request):
    """
    Get FAQs for a website via API
    """
    api_key = request.headers.get('X-Api-Key')
    if not api_key:
        return Response(
            {"error": "API key is required"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        website = Website.objects.get(api_key=api_key)
    except Website.DoesNotExist:
        return Response(
            {"error": "Invalid API key"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    faqs = website.faqs.filter(is_visible=True)
    serializer = FAQSerializer(faqs, many=True)
    
    return Response({
        "count": len(serializer.data),
        "results": serializer.data
    })

class WebsiteViewSet(viewsets.ModelViewSet):
    serializer_class = WebsiteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Website.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def regenerate_api_key(self, request, pk=None):
        website = self.get_object()
        website.api_key = website._generate_api_key()
        website.save()
        return Response({'api_key': website.api_key})

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsWebsiteOwner]

    def get_queryset(self):
        return Question.objects.filter(website__owner=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[HasValidAPIKey])
    def submit(self, request):
        website = request.auth
        
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            # Save the question
            question = serializer.save(website=website)
            
            # Send email notification to the website manager if email is provided
            if website.manager_email:
                subject = f"New Question from {website.name}"
                
                # Create HTML message
                html_message = render_to_string('emails/new_question.html', {
                    'website_name': website.name,
                    'question_text': question.question_text,
                    'user_email': question.user_email,
                    'dashboard_url': f"{request.build_absolute_uri('/accounts/dashboard/')}"
                })
                
                # Plain text version
                plain_message = strip_tags(html_message)
                
                # Send email in background thread
                send_email_in_thread(
                    subject=subject,
                    message=plain_message,
                    recipient_list=[website.manager_email],
                    html_message=html_message
                )
            
            return Response({'success': True, 'message': 'Question submitted successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def answer(self, request, pk=None):
        question = self.get_object()
        serializer = AnswerCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check if question already has an answer
            if hasattr(question, 'answer'):
                return Response(
                    {'detail': 'This question already has an answer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the answer
            answer = serializer.save(
                question=question,
                answered_by=request.user
            )
            
            # Send email to the user
            self._send_answer_email(question, answer)
            
            # Check if this should be added to FAQs
            self._check_for_faq(question, answer)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_answer_email(self, question, answer):
        subject = f'Your question has been answered - {question.website.name}'
        
        # Create HTML message
        html_message = render_to_string('emails/answer_notification.html', {
            'website_name': question.website.name,
            'question_text': question.question_text,
            'answer_text': answer.answer_text
        })
        
        # Plain text version
        plain_message = strip_tags(html_message)
        
        try:
            # Send email in background thread
            send_email_in_thread(
                subject=subject,
                message=plain_message,
                recipient_list=[question.user_email],
                html_message=html_message
            )
            answer.email_sent = True
            answer.save()
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error sending email: {e}")

    def _check_for_faq(self, question, answer):
        """
        Check if this question should be added to FAQs.
        Uses the comprehensive check_similar_questions function from faqs.utils.
        """
        from truelyfaq.faqs.utils import check_similar_questions
        
        try:
            # Mark the question as answered if not already
            if not question.is_answered:
                question.is_answered = True
                question.save(update_fields=['is_answered'])
            
            # Use the comprehensive check_similar_questions function
            faq = check_similar_questions(question)
            
            if faq:
                print(f"Question {question.id} added to FAQ {faq.id}")
                return faq
            else:
                print(f"Question {question.id} not added to any FAQ")
                return None
                
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error checking for FAQ: {e}")
            import traceback
            traceback.print_exc()
            return None

class FAQViewSet(viewsets.ModelViewSet):
    serializer_class = FAQSerializer
    
    def get_permissions(self):
        if self.action == 'list':
            return [HasValidAPIKey()]
        return [permissions.IsAuthenticated(), IsWebsiteOwner()]
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            # For authenticated users (website owners), show all FAQs
            return FAQ.objects.filter(website__owner=self.request.user)
        else:
            # For API key access, only show visible FAQs
            api_key = self.request.META.get('HTTP_X_API_KEY')
            website = get_object_or_404(Website, api_key=api_key)
            return FAQ.objects.filter(website=website, is_visible=True)
    
    @action(detail=True, methods=['patch'])
    def toggle_visibility(self, request, pk=None):
        faq = self.get_object()
        serializer = FAQVisibilitySerializer(faq, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
