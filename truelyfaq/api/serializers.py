from rest_framework import serializers
from truelyfaq.questions.models import Question, Answer
from truelyfaq.faqs.models import FAQ
from truelyfaq.accounts.models import Website

class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = ['id', 'name', 'url', 'api_key']
        read_only_fields = ['api_key']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'user_email', 'question_text', 'website']
        extra_kwargs = {
            'website': {'write_only': True}
        }
    
    def create(self, validated_data):
        return Question.objects.create(
            email=validated_data.get('email'),
            text=validated_data.get('question_text'),
            website_id=validated_data.get('website')
        )

class QuestionCreateSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    question_text = serializers.CharField()
    
    def create(self, validated_data):
        website = validated_data.pop('website')
        return Question.objects.create(
            user_email=validated_data.get('user_email'),  # Changed from email
            question_text=validated_data.get('question_text'),  # Changed from text
            website=website
        )

class AnswerCreateSerializer(serializers.Serializer):
    answer_text = serializers.CharField()
    
    def create(self, validated_data):
        question = validated_data.pop('question')
        answered_by = validated_data.pop('answered_by')
        
        # Mark the question as answered
        question.is_answered = True
        question.save()
        
        return Answer.objects.create(
            question=question,
            answer_text=validated_data.get('answer_text'),  # Changed from 'text' to 'answer_text'
            answered_by=answered_by
        )

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question_text', 'answer_text', 'created_at']

class FAQVisibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['is_visible']