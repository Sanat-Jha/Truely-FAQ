from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from truelyfaq.questions.models import Question
from truelyfaq.accounts.models import Website
from .serializers import QuestionSerializer, FAQSerializer, QuestionCreateSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_question(request):
    """
    Submit a question via API
    """
    # Add debugging
    print("Received question submission request")
    print(f"Headers: {request.headers}")
    print(f"Data: {request.data}")
    
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

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count
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
        serializer = QuestionCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Get the website from the API key
            api_key = request.META.get('HTTP_X_API_KEY')
            website = get_object_or_404(Website, api_key=api_key)
            
            # Create the question
            question = serializer.save(website=website)
            
            return Response(QuestionSerializer(question).data, status=status.HTTP_201_CREATED)
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
            print("Checking for FAQ...1")  # Debugging line
            self._check_for_faq(question, answer)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_answer_email(self, question, answer):
        subject = f'Your question has been answered - {question.website.name}'
        message = f"""
        Hello,

        Your question: "{question.question_text}"

        Has been answered: "{answer.answer_text}"

        Thank you for your inquiry!
        {question.website.name} Team
        """
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [question.user_email],
                fail_silently=False,
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
            print("Checking for FAQ...2")  # Debugging line
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
