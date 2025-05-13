from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import FAQ
from truelyfaq.questions.models import Question, Answer
from .utils import NLP_UTILITIES_AVAILABLE
from django.conf import settings

@login_required
def toggle_faq_visibility(request, faq_id):
    faq = get_object_or_404(FAQ, id=faq_id)
    
    # Check if the user owns the website
    if faq.website.owner != request.user:
        messages.error(request, "You don't have permission to manage this FAQ.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Toggle visibility
        faq.is_visible = not faq.is_visible
        faq.save()
        
        status = "visible" if faq.is_visible else "hidden"
        messages.success(request, f"FAQ is now {status}.")
    
    return redirect('website_detail', website_id=faq.website.id)

@login_required
def create_faq_manually(request, question_id):
    """Create an FAQ manually from a specific question"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check if the user owns the website
    if question.website.owner != request.user:
        messages.error(request, "You don't have permission to manage this question.")
        return redirect('dashboard')
    
    if not question.is_answered:
        messages.error(request, "Cannot create FAQ from unanswered question.")
        return redirect('question_detail', question_id=question_id)
    
    try:
        answer = Answer.objects.get(question=question)
    except Answer.DoesNotExist:
        messages.error(request, "Question is marked as answered but has no answer.")
        return redirect('question_detail', question_id=question_id)
    
    # Create the FAQ
    faq = FAQ.objects.create(
        website=question.website,
        question_text=question.question_text,
        answer_text=answer.answer_text,
        similarity_count=1
    )
    
    messages.success(request, "FAQ created successfully.")
    return redirect('website_detail', website_id=question.website.id)

@login_required
def find_similar_questions(request, website_id):
    """API endpoint to find similar questions using lightweight text similarity"""
    if request.method != 'POST' or 'question_text' not in request.POST:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    if not NLP_UTILITIES_AVAILABLE:
        return JsonResponse({'error': 'NLP utilities not available'}, status=503)
    
    question_text = request.POST['question_text']
    
    # Get existing questions for this website
    questions = Question.objects.filter(
        website_id=website_id,
        is_answered=True
    ).values('id', 'question_text')
    
    question_texts = [q['question_text'] for q in questions]
    question_ids = [q['id'] for q in questions]
    
    # Find similar questions
    similar_questions = []
    
    try:
        from .nlp_similarity import get_model, cosine_similarity
        
        # Get or create model
        model = get_model()
        
        if model:
            # Fit model on all questions plus the query
            all_texts = question_texts + [question_text]
            model.fit(all_texts)
            
            # Transform all texts to vectors
            vectors = model.transform(all_texts)
            
            # Get query vector (last one) and question vectors
            query_vector = vectors[-1]
            question_vectors = vectors[:-1]
            
            # Find similar questions
            threshold = getattr(settings, 'NLP_THRESHOLD', 0.7)
            
            for i, q_vector in enumerate(question_vectors):
                score = cosine_similarity(query_vector, q_vector)
                if score >= threshold:
                    similar_questions.append({
                        'id': question_ids[i],
                        'text': question_texts[i],
                        'score': round(score, 2)
                    })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({
        'similar_questions': similar_questions
    })
