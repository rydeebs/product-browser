"""
Trend detection using clustering and scoring algorithms
"""
from collections import defaultdict
from datetime import datetime, timedelta
import math

def cluster_opportunities(opportunities: list, similarity_threshold: float = 0.7) -> list:
    """
    Cluster similar opportunities together
    
    Args:
        opportunities: List of opportunity dictionaries
        similarity_threshold: Minimum similarity to cluster
    
    Returns:
        List of clustered opportunities with cluster IDs
    """
    clusters = []
    cluster_id = 0
    
    for opp in opportunities:
        assigned = False
        for cluster in clusters:
            if calculate_similarity(opp, cluster['representative']) >= similarity_threshold:
                cluster['opportunities'].append(opp)
                assigned = True
                break
        
        if not assigned:
            clusters.append({
                'cluster_id': cluster_id,
                'representative': opp,
                'opportunities': [opp]
            })
            cluster_id += 1
    
    return clusters

def calculate_similarity(opp1: dict, opp2: dict) -> float:
    """
    Calculate similarity between two opportunities
    
    Args:
        opp1, opp2: Opportunity dictionaries
    
    Returns:
        Similarity score (0-1)
    """
    # Simple keyword-based similarity
    keywords1 = set(opp1.get('keywords', []))
    keywords2 = set(opp2.get('keywords', []))
    
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = len(keywords1 & keywords2)
    union = len(keywords1 | keywords2)
    
    return intersection / union if union > 0 else 0.0

def calculate_confidence_score(opportunity: dict, evidence: list) -> float:
    """
    Calculate confidence score based on evidence
    
    Args:
        opportunity: Opportunity dictionary
        evidence: List of supporting evidence
    
    Returns:
        Confidence score (0-100)
    """
    base_score = 50.0
    
    # Increase score based on number of evidence
    evidence_bonus = min(len(evidence) * 5, 30)
    
    # Increase score based on recency
    recent_evidence = sum(1 for e in evidence 
                         if datetime.fromisoformat(e['created_at']) > 
                         datetime.now() - timedelta(days=7))
    recency_bonus = min(recent_evidence * 3, 20)
    
    return min(base_score + evidence_bonus + recency_bonus, 100.0)

def calculate_trend_score(opportunity: dict, time_window_days: int = 30) -> float:
    """
    Calculate trend score based on frequency over time
    
    Args:
        opportunity: Opportunity dictionary
        time_window_days: Time window to analyze
    
    Returns:
        Trend score (0-100)
    """
    # This would typically analyze frequency of mentions over time
    # For now, return a placeholder score
    return opportunity.get('mention_count', 0) * 10

