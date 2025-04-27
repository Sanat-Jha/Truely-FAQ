import logging
from django.db.models import Count
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

# Check if NLP utilities are available
try:
    from .nlp_similarity import find_similar_faq, check_question_frequency
    NLP_UTILITIES_AVAILABLE = True
    print("DEBUG: NLP utilities successfully imported")
    logger.info("NLP utilities are available")
except ImportError as e:
    NLP_UTILITIES_AVAILABLE = False
    print(f"DEBUG ERROR: Failed to import NLP utilities: {e}")
    logger.warning(f"NLP utilities are not available: {e}")

def check_similar_questions(question):
    """
    Check if there are similar questions and create an FAQ if needed.
    Uses only local NLP utilities (sentence transformers).
    
    Args:
        question: The Question object to check
        
    Returns:
        The matched or newly created FAQ object, or None
    """
    from .models import FAQ
    from truelyfaq.questions.models import Question, Answer
    
    print(f"DEBUG: Starting check_similar_questions for question ID {question.id}: '{question.question_text}'")
    
    # Basic validation
    if not question.is_answered:
        print(f"DEBUG: Question {question.id} is not answered. Skipping FAQ check.")
        logger.debug(f"Question {question.id} is not answered. Skipping FAQ check.")
        return None
    
    # Check if NLP utilities are available
    if not NLP_UTILITIES_AVAILABLE:
        print("DEBUG ERROR: NLP utilities not available. Skipping similarity check.")
        logger.warning("NLP utilities not available. Skipping similarity check.")
        return None
    
    # Check if the question has an answer
    try:
        answer = Answer.objects.get(question=question)
        print(f"DEBUG: Found answer for question {question.id}: '{answer.answer_text[:50]}...'")
    except Answer.DoesNotExist:
        print(f"DEBUG ERROR: Question {question.id} is marked as answered but has no answer object.")
        logger.warning(f"Question {question.id} is marked as answered but has no answer object.")
        return None
    
    website = question.website
    print(f"DEBUG: Processing for website: {website.name} (ID: {website.id})")
    
    # Check if the question is already associated with an FAQ
    # Since there's no direct relationship in the models, we need to create a field
    # to track this association
    
    # Get existing FAQs for this website
    existing_faqs = FAQ.objects.filter(website=website)
    print(f"DEBUG: Found {existing_faqs.count()} existing FAQs for website {website.id}")
    
    # Check against existing FAQs
    if existing_faqs.exists():
        faq_texts = list(existing_faqs.values_list('question_text', flat=True))
        print(f"DEBUG: Checking against {len(faq_texts)} existing FAQ questions")
        
        # Find similar FAQ
        print(f"DEBUG: Calling find_similar_faq with threshold={getattr(settings, 'NLP_THRESHOLD', 0.7)}")
        similar_faq_index = find_similar_faq(
            query_question=question.question_text,
            faq_list=faq_texts,
            threshold=getattr(settings, 'NLP_THRESHOLD', 0.7)
        )
        print(f"DEBUG: find_similar_faq returned index: {similar_faq_index}")
        
        if similar_faq_index != -1:
            # Found a similar FAQ
            matched_faq = existing_faqs[similar_faq_index]
            print(f"DEBUG: Question {question.id} matches existing FAQ {matched_faq.id}: '{matched_faq.question_text}'")
            logger.info(f"Question {question.id} matches existing FAQ {matched_faq.id}")
            
            # Update similarity count
            matched_faq.similarity_count += 1
            matched_faq.save(update_fields=['similarity_count'])
            print(f"DEBUG: Updated FAQ {matched_faq.id} similarity count to {matched_faq.similarity_count}")
            
            return matched_faq
    
    # If no existing FAQ match, check if it should be a new FAQ
    existing_questions = Question.objects.filter(
        website=website,
        is_answered=True
    ).exclude(id=question.id)
    
    print(f"DEBUG: Found {existing_questions.count()} existing answered questions to check frequency against")
    
    if existing_questions.exists():
        question_texts = list(existing_questions.values_list('question_text', flat=True))
        
        # Check if this question is similar to multiple existing questions
        print(f"DEBUG: Calling check_question_frequency with threshold={getattr(settings, 'NLP_THRESHOLD', 0.7)}")
        is_frequent, similar_count = check_question_frequency(
            query_question=question.question_text,
            question_list=question_texts,
            threshold=getattr(settings, 'NLP_THRESHOLD', 0.7)
        )
        print(f"DEBUG: check_question_frequency returned: is_frequent={is_frequent}, similar_count={similar_count}")
        
        min_similar = getattr(settings, 'NLP_MIN_SIMILAR_FOR_NEW_FAQ', 1)
        print(f"DEBUG: Minimum similar questions required: {min_similar}")
        
        if is_frequent and similar_count >= min_similar:
            # Create a new FAQ
            faq = FAQ.objects.create(
                website=website,
                question_text=question.question_text,
                answer_text=answer.answer_text,
                similarity_count=similar_count + 1  # +1 for the current question
            )
            print(f"DEBUG: Created new FAQ {faq.id} with similarity count {similar_count+1}")
            
            logger.info(f"Created new FAQ {faq.id} from question {question.id} with similarity count {similar_count+1}")
            return faq
        else:
            print(f"DEBUG: Not creating FAQ. is_frequent={is_frequent}, similar_count={similar_count}, min_required={min_similar}")
    else:
        print("DEBUG: No existing answered questions to compare with")
    
    print(f"DEBUG: Question {question.id} not added to any FAQ")
    logger.debug(f"Question {question.id} not added to any FAQ")
    return None