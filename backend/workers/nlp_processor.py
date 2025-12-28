"""
NLP processing using spaCy for keyword extraction and entity recognition
"""
import spacy
from collections import Counter
import re

# Load spaCy model (run: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

def extract_keywords(text: str, max_keywords: int = 10) -> list:
    """
    Extract keywords from text using NLP
    
    Args:
        text: Text to analyze
        max_keywords: Maximum number of keywords to return
    
    Returns:
        List of keyword tuples (keyword, frequency)
    """
    if not nlp:
        # Fallback to simple word frequency
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        return Counter(words).most_common(max_keywords)
    
    doc = nlp(text)
    
    # Extract nouns and adjectives (most relevant for product opportunities)
    keywords = []
    for token in doc:
        if token.pos_ in ['NOUN', 'ADJ'] and not token.is_stop and not token.is_punct:
            keywords.append(token.lemma_.lower())
    
    return Counter(keywords).most_common(max_keywords)

def extract_entities(text: str) -> dict:
    """
    Extract named entities from text
    
    Args:
        text: Text to analyze
    
    Returns:
        Dictionary of entity types and their values
    """
    if not nlp:
        return {}
    
    doc = nlp(text)
    entities = {
        'PRODUCT': [],
        'ORG': [],
        'PERSON': [],
        'MONEY': [],
        'DATE': []
    }
    
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text)
    
    return {k: list(set(v)) for k, v in entities.items() if v}

def calculate_relevance_score(text: str, keywords: list) -> float:
    """
    Calculate relevance score based on keyword density
    
    Args:
        text: Text to score
        keywords: List of relevant keywords
    
    Returns:
        Relevance score (0-1)
    """
    if not keywords:
        return 0.0
    
    text_lower = text.lower()
    keyword_count = sum(1 for keyword, _ in keywords if keyword in text_lower)
    
    return min(keyword_count / len(keywords), 1.0)

