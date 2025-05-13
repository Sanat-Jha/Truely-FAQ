import logging
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

# Check if NLP utilities are available
try:
    from .nlp_similarity import find_similar_faq, check_question_frequency, get_model
    # Check if model can be loaded
    model = get_model()
    NLP_UTILITIES_AVAILABLE = model is not None
    if NLP_UTILITIES_AVAILABLE:
        logger.info("NLP utilities are available with local model")
    else:
        logger.warning("NLP utilities are not available: Could not load model")
except ImportError as e:
    NLP_UTILITIES_AVAILABLE = False
    logger.warning(f"NLP utilities are not available: {e}")

def check_similar_questions(question):
    """
    Check if there are similar questions and create an FAQ if needed.
    Uses local sentence-transformers model for semantic similarity.
    
    Args:
        question: The Question object to check
        
    Returns:
        The matched or newly created FAQ object, or None
    """
    from .models import FAQ
    from truelyfaq.questions.models import Question, Answer
    
    logger.debug(f"Starting check_similar_questions for question ID {question.id}: '{question.question_text}'")
    
    # Basic validation
    if not question.is_answered:
        logger.debug(f"Question {question.id} is not answered. Skipping FAQ check.")
        return None
    
    # Check if NLP utilities are available
    if not NLP_UTILITIES_AVAILABLE:
        logger.warning("NLP utilities not available. Skipping similarity check.")
        return None
    
    # Check if the question has an answer
    try:
        answer = Answer.objects.get(question=question)
    except Answer.DoesNotExist:
        logger.warning(f"Question {question.id} is marked as answered but has no answer object.")
        return None
    
    website = question.website
    
    # Get existing FAQs for this website
    existing_faqs = FAQ.objects.filter(website=website)
    
    # Check against existing FAQs
    if existing_faqs.exists():
        faq_texts = list(existing_faqs.values_list('question_text', flat=True))
        
        # Find similar FAQ
        similar_faq_index = find_similar_faq(
            query_question=question.question_text,
            faq_list=faq_texts,
            threshold=getattr(settings, 'NLP_THRESHOLD', 0.7)
        )
        
        if similar_faq_index != -1:
            # Found a similar FAQ
            matched_faq = existing_faqs[similar_faq_index]
            logger.info(f"Question {question.id} matches existing FAQ {matched_faq.id}")
            
            # Update similarity count
            matched_faq.similarity_count += 1
            matched_faq.save(update_fields=['similarity_count'])
            
            return matched_faq
    
    # If no existing FAQ match, check if it should be a new FAQ
    existing_questions = Question.objects.filter(
        website=website,
        is_answered=True
    ).exclude(id=question.id)
    
    if existing_questions.exists():
        question_texts = list(existing_questions.values_list('question_text', flat=True))
        
        # Check if this question is similar to multiple existing questions
        is_frequent, similar_count = check_question_frequency(
            query_question=question.question_text,
            question_list=question_texts,
            threshold=getattr(settings, 'NLP_THRESHOLD', 0.7)
        )
        
        min_similar = getattr(settings, 'NLP_MIN_SIMILAR_FOR_NEW_FAQ', 1)
        
        if is_frequent and similar_count >= min_similar:
            # Create a new FAQ
            faq = FAQ.objects.create(
                website=website,
                question_text=question.question_text,
                answer_text=answer.answer_text,
                similarity_count=similar_count + 1  # +1 for the current question
            )
            
            logger.info(f"Created new FAQ {faq.id} from question {question.id} with similarity count {similar_count+1}")
            return faq
    
    logger.debug(f"Question {question.id} not added to any FAQ")
    return None