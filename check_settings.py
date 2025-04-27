import os
import sys
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truelyfaq.settings')
django.setup()

# Check required settings
required_settings = [
    'NLP_UTILITIES_AVAILABLE',
    'NLP_THRESHOLD',
    'NLP_MIN_SIMILAR_FOR_NEW_FAQ'
]

print("=== CHECKING REQUIRED SETTINGS ===")
all_ok = True

for setting_name in required_settings:
    if hasattr(settings, setting_name):
        value = getattr(settings, setting_name)
        print(f"✓ {setting_name}: {value}")
    else:
        print(f"✗ {setting_name} is missing")
        all_ok = False

if all_ok:
    print("\nAll required settings are configured.")
else:
    print("\nSome required settings are missing. Please check your settings.py file.")

# Check for NLP libraries
print("\n=== CHECKING NLP LIBRARIES ===")
try:
    import sentence_transformers
    print("✓ sentence_transformers is installed")
    
    # Try to import the specific model to verify it's available
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ SentenceTransformer model loaded successfully")
    except Exception as e:
        print(f"✗ Error loading SentenceTransformer model: {e}")
        all_ok = False
        
except ImportError:
    print("✗ sentence_transformers is not installed")
    all_ok = False

# Suggest fixes
if not all_ok:
    print("\n=== SUGGESTED FIXES ===")
    print("1. Install required packages:")
    print("   pip install sentence-transformers")
    print("2. Add missing settings to your settings.py file:")
    print("   NLP_UTILITIES_AVAILABLE = True")
    print("   NLP_THRESHOLD = 0.7  # Adjust as needed")
    print("   NLP_MIN_SIMILAR_FOR_NEW_FAQ = 1  # Adjust as needed")