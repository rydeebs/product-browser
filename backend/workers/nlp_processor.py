"""
NLP processing using spaCy for keyword extraction and entity recognition
Includes TF-IDF scoring and noun phrase extraction
"""
import spacy
from collections import Counter
import re
import math

# Load spaCy model (run: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

# Try to import sklearn for TF-IDF (optional)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    print("Warning: scikit-learn not found. TF-IDF scoring disabled.")
    HAS_SKLEARN = False


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


def extract_noun_phrases(text: str, max_phrases: int = 10) -> list:
    """
    Extract noun phrases from text (e.g., "smart water bottle", "pet medication tracker")
    
    Args:
        text: Text to analyze
        max_phrases: Maximum number of phrases to return
    
    Returns:
        List of noun phrase tuples (phrase, frequency)
    """
    if not nlp:
        return []
    
    doc = nlp(text)
    
    # Extract noun chunks (noun phrases)
    phrases = []
    for chunk in doc.noun_chunks:
        # Clean up the phrase
        phrase = chunk.lemma_.lower().strip()
        # Filter out very short or very long phrases
        if 2 <= len(phrase.split()) <= 5 and len(phrase) > 3:
            phrases.append(phrase)
    
    return Counter(phrases).most_common(max_phrases)


def extract_keywords_tfidf(texts: list, max_keywords: int = 10) -> dict:
    """
    Extract keywords using TF-IDF scoring across multiple documents
    Better for finding unique/important terms in a corpus
    
    Args:
        texts: List of text documents
        max_keywords: Maximum keywords per document
    
    Returns:
        Dictionary mapping document index to list of (keyword, score) tuples
    """
    if not HAS_SKLEARN or not texts:
        return {}
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        ngram_range=(1, 2),  # Include bigrams
        min_df=1,
        max_df=0.95
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        results = {}
        for doc_idx in range(len(texts)):
            # Get TF-IDF scores for this document
            doc_vector = tfidf_matrix[doc_idx].toarray().flatten()
            
            # Get top keywords by score
            top_indices = doc_vector.argsort()[-max_keywords:][::-1]
            keywords = [
                (feature_names[i], float(doc_vector[i])) 
                for i in top_indices 
                if doc_vector[i] > 0
            ]
            results[doc_idx] = keywords
        
        return results
        
    except Exception as e:
        print(f"TF-IDF error: {e}")
        return {}


def extract_keywords_advanced(text: str, max_keywords: int = 10) -> dict:
    """
    Advanced keyword extraction combining multiple methods
    
    Args:
        text: Text to analyze
        max_keywords: Maximum keywords to return
    
    Returns:
        Dictionary with different keyword types
    """
    results = {
        'single_keywords': [],
        'noun_phrases': [],
        'entities': {},
        'all_keywords': []
    }
    
    # Basic keyword extraction
    results['single_keywords'] = extract_keywords(text, max_keywords)
    
    # Noun phrase extraction
    results['noun_phrases'] = extract_noun_phrases(text, max_keywords)
    
    # Entity extraction
    results['entities'] = extract_entities(text)
    
    # Combine all keywords (deduplicated)
    all_kw = set()
    for kw, _ in results['single_keywords']:
        all_kw.add(kw)
    for phrase, _ in results['noun_phrases']:
        all_kw.add(phrase)
    for entity_type, entities in results['entities'].items():
        for entity in entities:
            all_kw.add(entity.lower())
    
    results['all_keywords'] = list(all_kw)[:max_keywords]
    
    return results

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


def test_nlp_processor():
    """Test the NLP processor with sample Reddit posts"""
    
    sample_posts = [
        "I wish there was a smart water bottle that could track how much I drink throughout the day. I always forget to stay hydrated.",
        "Why isn't there a good app for tracking my pet's medications? I have 3 dogs and always forget who got what and when.",
        "Looking for a better solution for organizing my home office cables. Everything is a tangled mess behind my desk.",
        "Frustrated with my current meal prep containers. They leak, don't stack well, and the lids never fit properly.",
        "Does anyone know of a product that helps with back pain from sitting all day? My ergonomic chair isn't cutting it.",
        "I need a better way to track my kids' chores and allowance. Spreadsheets are too complicated for them.",
        "Why doesn't anyone make a quiet blender? I want to make smoothies early morning without waking everyone up.",
        "Sick of my phone dying during long hikes. Solar chargers are too slow and bulky.",
        "There should be a smart pet feeder that can handle wet food, not just kibble.",
        "Looking for recommendations for a standing desk mat. My feet hurt after standing for a few hours."
    ]
    
    print("🧪 Testing NLP Processor with 10 Reddit posts...\n")
    print("=" * 60)
    
    for i, post in enumerate(sample_posts, 1):
        print(f"\n📝 Post {i}: {post[:60]}...")
        print("-" * 40)
        
        # Extract keywords
        keywords = extract_keywords(post, max_keywords=5)
        print(f"🔑 Keywords: {[kw for kw, _ in keywords]}")
        
        # Extract noun phrases
        phrases = extract_noun_phrases(post, max_phrases=3)
        print(f"📦 Noun Phrases: {[p for p, _ in phrases]}")
        
        # Extract entities
        entities = extract_entities(post)
        if entities:
            print(f"🏷️  Entities: {entities}")
        
        # Advanced extraction
        advanced = extract_keywords_advanced(post, max_keywords=8)
        print(f"🎯 All Keywords: {advanced['all_keywords'][:5]}")
    
    print("\n" + "=" * 60)
    
    # Test TF-IDF across all posts
    if HAS_SKLEARN:
        print("\n📊 TF-IDF Analysis (corpus-wide):")
        print("-" * 40)
        tfidf_results = extract_keywords_tfidf(sample_posts, max_keywords=5)
        for doc_idx, keywords in list(tfidf_results.items())[:3]:
            print(f"Post {doc_idx + 1}: {[kw for kw, score in keywords]}")
    
    print("\n✅ NLP Processor test complete!")


if __name__ == '__main__':
    test_nlp_processor()

