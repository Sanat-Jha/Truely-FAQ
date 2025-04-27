# your_app_name/utils/nlp_similarity.py

import logging
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer, util

# Configure logging - Django will often handle the root configuration
logger = logging.getLogger(__name__)

# --- Global Configuration ---
# Consider moving MODEL_NAME to your Django settings.py for easier configuration
MODEL_NAME = 'all-MiniLM-L6-v2'
DEFAULT_SIMILARITY_THRESHOLD = 0.7

# --- Global Model Instance ---
# Load the model once when the Django application starts (when this module is imported).
# This prevents reloading the model on every request, which is performance-critical.
try:
    # Load the specified pre-trained Sentence Transformer model globally
    print(f"DEBUG: Loading Sentence Transformer model: {MODEL_NAME}")
    nlp_model = SentenceTransformer(MODEL_NAME)
    print(f"DEBUG: Successfully loaded Sentence Transformer model: {MODEL_NAME}")
    logger.info(f"Successfully loaded Sentence Transformer model: {MODEL_NAME}")
except Exception as e:
    # Log a critical error if the model fails to load.
    # The functions below will check if nlp_model is None.
    print(f"DEBUG ERROR: Failed to load Sentence Transformer model '{MODEL_NAME}'. Error: {e}")
    logger.error(
        f"CRITICAL: Failed to load Sentence Transformer model '{MODEL_NAME}'. "
        f"NLP similarity features will be unavailable. Error: {e}",
        exc_info=True # Include traceback in the log
    )
    nlp_model = None

# --- Utility Functions ---

def find_similar_faq(
    query_question: str,
    faq_list: List[str],
    threshold: Optional[float] = None
) -> int:
    """
    Finds the index of the most similar FAQ question based on semantic meaning.

    Args:
        query_question (str): The input question string.
        faq_list (list[str]): A list of FAQ question strings.
        threshold (float, optional): The minimum cosine similarity score (0-1).
                                     Defaults to DEFAULT_SIMILARITY_THRESHOLD.

    Returns:
        int: The index (position) of the most similar FAQ in the faq_list.
             Returns -1 if no FAQ meets the threshold or if the model failed to load.
    """
    print(f"DEBUG: find_similar_faq called with query: '{query_question[:50]}...'")
    print(f"DEBUG: FAQ list contains {len(faq_list)} items")
    
    # Return -1 immediately if the FAQ list is empty
    if not faq_list:
        print("DEBUG: FAQ list is empty, returning -1")
        return -1

    current_threshold = threshold if threshold is not None else DEFAULT_SIMILARITY_THRESHOLD
    print(f"DEBUG: Using similarity threshold: {current_threshold}")

    try:
        # Load the model for each function call (like in the working code)
        print(f"DEBUG: Loading Sentence Transformer model: {MODEL_NAME}")
        model = SentenceTransformer(MODEL_NAME)
        
        # Convert the input question and all FAQ questions into embeddings
        print("DEBUG: Generating embeddings for query question")
        query_embedding = model.encode(query_question, convert_to_tensor=True)
        print("DEBUG: Generating embeddings for FAQ list")
        faq_embeddings = model.encode(faq_list, convert_to_tensor=True)

        # Calculate cosine similarities
        print("DEBUG: Calculating cosine similarities")
        cosine_scores = util.cos_sim(query_embedding, faq_embeddings)

        # Find the highest score and its index
        best_match_index = cosine_scores[0].argmax().item()
        best_match_score = cosine_scores[0][best_match_index].item()
        print(f"DEBUG: Best match index: {best_match_index}, score: {best_match_score}")

        # Check against threshold
        if best_match_score >= current_threshold:
            print(f"DEBUG: Match found! Index: {best_match_index}, Score: {best_match_score}")
            return best_match_index
        else:
            print(f"DEBUG: Best match score {best_match_score} below threshold {current_threshold}")
            return -1
    except Exception as e:
        print(f"DEBUG ERROR: Error during FAQ similarity calculation: {e}")
        logger.error(f"Error during FAQ similarity calculation: {e}", exc_info=True)
        return -1 # Return -1 on error


def check_question_frequency(
    query_question: str,
    question_list: List[str],
    threshold: Optional[float] = None
) -> Tuple[bool, int]:
    """
    Checks if a question is semantically similar to others in a given list
    and counts how many similar questions exist.

    Args:
        query_question (str): The input question string.
        question_list (list[str]): A list of question strings to compare against.
        threshold (float, optional): The minimum cosine similarity score to consider
                                     another question as "similar".
                                     Defaults to DEFAULT_SIMILARITY_THRESHOLD.

    Returns:
        tuple[bool, int]: A tuple containing:
               - bool: True if at least one similar question (above threshold)
                       is found in the list, False otherwise.
               - int: The total count of questions in the list considered similar.
    """
    print(f"DEBUG: check_question_frequency called with query: '{query_question[:50]}...'")
    print(f"DEBUG: Question list contains {len(question_list)} items")
    
    # Return (False, 0) immediately if the comparison list is empty
    if not question_list:
        print("DEBUG: Question list is empty, returning False, 0")
        return False, 0

    current_threshold = threshold if threshold is not None else DEFAULT_SIMILARITY_THRESHOLD
    print(f"DEBUG: Using similarity threshold: {current_threshold}")

    try:
        # Load the model for each function call (like in the working code)
        print(f"DEBUG: Loading Sentence Transformer model: {MODEL_NAME}")
        model = SentenceTransformer(MODEL_NAME)
        
        # Generate embeddings
        print("DEBUG: Generating embeddings for query question")
        query_embedding = model.encode(query_question, convert_to_tensor=True)
        print("DEBUG: Generating embeddings for question list")
        list_embeddings = model.encode(question_list, convert_to_tensor=True)

        # Calculate cosine similarities
        print("DEBUG: Calculating cosine similarities")
        cosine_scores = util.cos_sim(query_embedding, list_embeddings)

        # Count similar questions above the threshold
        similar_count = 0
        print("DEBUG: Checking similarity scores against threshold")
        for i in range(len(question_list)):
            score = cosine_scores[0][i].item()
            if score >= current_threshold:
                similar_count += 1
                print(f"DEBUG: Similar question found at index {i}: '{question_list[i][:50]}...', score: {score}")

        # Determine if frequent (at least one similar found)
        is_frequent = similar_count > 0
        print(f"DEBUG: Final result: is_frequent={is_frequent}, similar_count={similar_count}")

        return is_frequent, similar_count
    except Exception as e:
        print(f"DEBUG ERROR: Error during question frequency calculation: {e}")
        logger.error(f"Error during question frequency calculation: {e}", exc_info=True)
        return False, 0 # Return False, 0 on error

