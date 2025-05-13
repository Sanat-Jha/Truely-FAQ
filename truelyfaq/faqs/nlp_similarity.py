# truelyfaq/faqs/nlp_similarity.py

import logging
import re
import math
from typing import List, Tuple, Optional
from collections import Counter
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

# --- Global Configuration ---
DEFAULT_SIMILARITY_THRESHOLD = 0.7

# --- TF-IDF Implementation ---
class SimpleTFIDF:
    """A lightweight TF-IDF implementation without external dependencies"""
    
    def __init__(self):
        self.document_count = 0
        self.vocabulary = {}
        self.idf = {}
        self.documents = []
        
    def preprocess(self, text):
        """Simple text preprocessing"""
        # Convert to lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        # Split into words
        return text.split()
        
    def fit(self, documents):
        """Fit the TF-IDF model on a list of documents"""
        self.documents = [self.preprocess(doc) for doc in documents]
        self.document_count = len(self.documents)
        
        # Build vocabulary and document frequency
        doc_frequency = Counter()
        for doc in self.documents:
            # Count each word only once per document
            words_in_doc = set(doc)
            for word in words_in_doc:
                doc_frequency[word] += 1
        
        # Calculate IDF for each word
        self.vocabulary = {word: idx for idx, word in enumerate(doc_frequency.keys())}
        self.idf = {word: math.log(self.document_count / (freq + 1)) + 1 
                   for word, freq in doc_frequency.items()}
        
    def transform(self, documents):
        """Transform documents to TF-IDF vectors"""
        if not isinstance(documents, list):
            documents = [documents]
            
        preprocessed = [self.preprocess(doc) for doc in documents]
        result = []
        
        for doc in preprocessed:
            # Calculate term frequency
            tf = Counter(doc)
            
            # Create TF-IDF vector
            tfidf_vector = [0] * len(self.vocabulary)
            for word, count in tf.items():
                if word in self.vocabulary:
                    idx = self.vocabulary[word]
                    tfidf_vector[idx] = count * self.idf.get(word, 0)
            
            # Normalize vector
            magnitude = math.sqrt(sum(v * v for v in tfidf_vector))
            if magnitude > 0:
                tfidf_vector = [v / magnitude for v in tfidf_vector]
                
            result.append(tfidf_vector)
            
        return result

# --- Global Model Instance ---
_tfidf_model = None

def get_model():
    """Get or initialize the TF-IDF model"""
    global _tfidf_model
    if _tfidf_model is None:
        try:
            _tfidf_model = SimpleTFIDF()
            logger.info("Initialized lightweight TF-IDF model")
        except Exception as e:
            logger.error(f"Failed to initialize TF-IDF model: {e}", exc_info=True)
            return None
    return _tfidf_model

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    return dot_product  # Vectors are already normalized

def find_similar_faq(
    query_question: str,
    faq_list: List[str],
    threshold: Optional[float] = None
) -> int:
    """
    Finds the index of the most similar FAQ question based on text similarity.

    Args:
        query_question (str): The input question string.
        faq_list (list[str]): A list of FAQ question strings.
        threshold (float, optional): The minimum similarity score (0-1).
                                     Defaults to DEFAULT_SIMILARITY_THRESHOLD.

    Returns:
        int: The index (position) of the most similar FAQ in the faq_list.
             Returns -1 if no FAQ meets the threshold.
    """
    logger.debug(f"find_similar_faq called with query: '{query_question[:50]}...'")
    
    # Return -1 immediately if the FAQ list is empty
    if not faq_list:
        logger.debug("FAQ list is empty, returning -1")
        return -1

    current_threshold = threshold if threshold is not None else DEFAULT_SIMILARITY_THRESHOLD
    
    try:
        # Get or create model
        model = get_model()
        
        # Fit model on FAQ list plus query
        all_texts = faq_list + [query_question]
        model.fit(all_texts)
        
        # Transform all texts to vectors
        vectors = model.transform(all_texts)
        
        # Get query vector (last one) and FAQ vectors
        query_vector = vectors[-1]
        faq_vectors = vectors[:-1]
        
        # Find best match
        best_match_index = -1
        best_match_score = -1
        
        for i, faq_vector in enumerate(faq_vectors):
            score = cosine_similarity(query_vector, faq_vector)
            
            if score > best_match_score:
                best_match_score = score
                best_match_index = i
        
        # Check against threshold
        if best_match_score >= current_threshold:
            logger.debug(f"Match found! Index: {best_match_index}, Score: {best_match_score}")
            return best_match_index
        else:
            logger.debug(f"Best match score {best_match_score} below threshold {current_threshold}")
            return -1
    except Exception as e:
        logger.error(f"Error during FAQ similarity calculation: {e}", exc_info=True)
        return -1

def check_question_frequency(
    query_question: str,
    question_list: List[str],
    threshold: Optional[float] = None
) -> Tuple[bool, int]:
    """
    Checks if a question is similar to others in a given list
    and counts how many similar questions exist.

    Args:
        query_question (str): The input question string.
        question_list (list[str]): A list of question strings to compare against.
        threshold (float, optional): The minimum similarity score to consider
                                     another question as "similar".
                                     Defaults to DEFAULT_SIMILARITY_THRESHOLD.

    Returns:
        tuple[bool, int]: A tuple containing:
               - bool: True if at least one similar question (above threshold)
                       is found in the list, False otherwise.
               - int: The total count of questions in the list considered similar.
    """
    logger.debug(f"check_question_frequency called with query: '{query_question[:50]}...'")
    
    # Return (False, 0) immediately if the comparison list is empty
    if not question_list:
        logger.debug("Question list is empty, returning False, 0")
        return False, 0

    current_threshold = threshold if threshold is not None else DEFAULT_SIMILARITY_THRESHOLD
    
    try:
        # Get or create model
        model = get_model()
        
        # Fit model on question list plus query
        all_texts = question_list + [query_question]
        model.fit(all_texts)
        
        # Transform all texts to vectors
        vectors = model.transform(all_texts)
        
        # Get query vector (last one) and question vectors
        query_vector = vectors[-1]
        question_vectors = vectors[:-1]
        
        # Count similar questions
        similar_count = 0
        
        for i, question_vector in enumerate(question_vectors):
            score = cosine_similarity(query_vector, question_vector)
            
            if score >= current_threshold:
                similar_count += 1
                logger.debug(f"Similar question found at index {i}, score: {score}")
        
        # Determine if frequent (at least one similar found)
        is_frequent = similar_count > 0
        logger.debug(f"Final result: is_frequent={is_frequent}, similar_count={similar_count}")
        
        return is_frequent, similar_count
    except Exception as e:
        logger.error(f"Error during question frequency calculation: {e}", exc_info=True)
        return False, 0

