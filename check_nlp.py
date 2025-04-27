import os
import sys
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truelyfaq.settings')
django.setup()

# Now check NLP utilities
print("Checking NLP utilities configuration...")
print(f"NLP_UTILITIES_AVAILABLE: {getattr(settings, 'NLP_UTILITIES_AVAILABLE', False)}")
print(f"NLP_THRESHOLD: {getattr(settings, 'NLP_THRESHOLD', 'Not set')}")
print(f"NLP_MIN_SIMILAR_FOR_NEW_FAQ: {getattr(settings, 'NLP_MIN_SIMILAR_FOR_NEW_FAQ', 'Not set')}")

# Try to import the NLP utilities
try:
    from truelyfaq.faqs.utils import find_similar_faq, check_question_frequency
    print("✓ Successfully imported NLP utility functions")
    
    # Test if they work with a simple example
    try:
        result = find_similar_faq("Test question", ["Sample FAQ 1", "Sample FAQ 2"], 0.5)
        print(f"✓ find_similar_faq function works (returned: {result})")
    except Exception as e:
        print(f"✗ Error testing find_similar_faq: {str(e)}")
    
    try:
        is_frequent, count = check_question_frequency("Test question", ["Similar question", "Different question"], 0.5)
        print(f"✓ check_question_frequency function works (returned: is_frequent={is_frequent}, count={count})")
    except Exception as e:
        print(f"✗ Error testing check_question_frequency: {str(e)}")
        
except ImportError as e:
    print(f"✗ Failed to import NLP utility functions: {str(e)}")