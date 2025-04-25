from django.db.models import Count
from django.conf import settings

def check_similar_questions(question):
    """
    Check if there are similar questions and create an FAQ if needed.
    """
    from .models import FAQ
    from truelyfaq.questions.models import Question
    from groq import Groq
    
    if not question.is_answered:
        return
    
    website = question.website
    
    if hasattr(question, 'faq'):
        return
    
    # First check if question belongs to existing FAQs
    existing_faqs = FAQ.objects.filter(website=website)
    if existing_faqs.exists():
        # Update FAQ listing format
        faqs_list = "\n".join([f"FAQ {i+1}:\nQ: {faq.question_text}\nA: {faq.answer_text}" 
                              for i, faq in enumerate(existing_faqs)])
        
        existing_faq_prompt = f"""
        Does this question belong to any of these existing FAQs? 
        Question: '{question.question_text}'
        
        Existing FAQs:
        {faqs_list}
        
        Respond in format: Yes,FAQ number / No
        Example: 'Yes,2' if it belongs to FAQ 2, or 'No' if it doesn't belong to any.
        """
        
        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": existing_faq_prompt}],
                model="llama-3.3-70b-versatile",
                stream=False,
            )
            
            response = chat_completion.choices[0].message.content.strip()
            if response.startswith('Yes'):
                faq_num = int(response.split(',')[1]) - 1
                faq = existing_faqs[faq_num]
                
                # Update similarity count when adding to existing FAQ
                faq.similarity_count = faq.similarity_count + 1
                faq.save()
                
                question.faq = faq
                question.save()
                return faq
        
        except Exception as e:
            print(f"Error checking existing FAQs: {e}")
    
    # If no existing FAQ match, check if it should be a new FAQ
    existing_questions = Question.objects.filter(
        website=website,
        is_answered=True
    ).exclude(id=question.id).values_list('question_text', flat=True)
    
    questions_list = "\n".join([f"- {q}" for q in existing_questions])
    
    new_faq_prompt = f"""
    Is this question '{question.question_text}' similar to any of these questions? If yes, how many?
    
    Existing questions:
    {questions_list}
    
    Respond in format: Yes/count or No/0
    Example: 'Yes/3' if similar to 3 questions, or 'No/0' if not similar.
    """
    
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": new_faq_prompt}],
            model="llama-3.3-70b-versatile",
            stream=False,
        )
        
        response = chat_completion.choices[0].message.content.strip()
        result, count = response.split('/')
        count = int(count)
        
        if result.lower() == 'yes' and count > 0:
            # Update FAQ creation
            faq = FAQ.objects.create(
                website=website,
                question_text=question.question_text,
                answer_text=question.answer.answer_text,
                is_visible=True,
                similarity_count=count
            )
            
            question.faq = faq
            question.save()
            
            for similar_q in Question.objects.filter(question_text__in=existing_questions):
                similar_q.faq = faq
                similar_q.save()
            
            return faq
            
    except Exception as e:
        print(f"Error in Groq AI processing: {e}")
    
    return None