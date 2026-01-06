import os
from collections import defaultdict, Counter
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)


# ============================================================
# DATA FETCHING
# ============================================================

def get_high_pain_analyses():
    """Get analyses with pain >= 7"""
    result = supabase.table('post_analysis')\
        .select('*, raw_posts(*)')\
        .gte('pain_severity', 7)\
        .execute()
    
    return result.data


# ============================================================
# CLUSTERING
# ============================================================

def cluster_by_keywords(analyses):
    """Group similar problems by overlapping keywords"""
    clusters = []
    used = set()
    
    for i, analysis in enumerate(analyses):
        if i in used:
            continue
            
        cluster = [analysis]
        cluster_keywords = set(analysis.get('keywords', []))
        used.add(i)
        
        # Find similar analyses
        for j, other in enumerate(analyses[i+1:], start=i+1):
            if j in used:
                continue
                
            other_keywords = set(other.get('keywords', []))
            overlap = len(cluster_keywords & other_keywords)
            
            # If 2+ keywords match, group together
            if overlap >= 2:
                cluster.append(other)
                cluster_keywords.update(other_keywords)
                used.add(j)
        
        clusters.append(cluster)
    
    return clusters


# ============================================================
# TITLE GENERATION FROM KEYWORDS
# ============================================================

def generate_title_from_keywords(cluster) -> str:
    """
    Generate a descriptive title from the most common keywords in the cluster.
    
    Strategy:
    1. Count keyword frequency across all analyses
    2. Pick top 2-3 most relevant keywords
    3. Create a readable title format
    
    Args:
        cluster: List of analysis dictionaries with 'keywords' field
    
    Returns:
        Generated title string (max 100 chars)
    """
    # Count all keywords across cluster
    keyword_counts = Counter()
    
    for analysis in cluster:
        keywords = analysis.get('keywords', [])
        for keyword in keywords:
            # Clean and normalize keyword
            keyword = keyword.strip().lower()
            if keyword and len(keyword) > 2:  # Skip very short words
                keyword_counts[keyword] += 1
    
    if not keyword_counts:
        # Fallback to problem summary if no keywords
        return cluster[0].get('problem_summary', 'Untitled Opportunity')[:100]
    
    # Get top keywords (most frequent)
    top_keywords = keyword_counts.most_common(5)
    
    # Filter out generic words
    generic_words = {'product', 'thing', 'stuff', 'something', 'anyone', 'people', 'need', 'want', 'looking'}
    filtered_keywords = [(kw, count) for kw, count in top_keywords if kw not in generic_words]
    
    if not filtered_keywords:
        filtered_keywords = top_keywords[:3]
    
    # Take top 2-3 keywords for title
    title_keywords = [kw.title() for kw, _ in filtered_keywords[:3]]
    
    # Create title based on number of keywords
    if len(title_keywords) == 1:
        title = f"{title_keywords[0]} Solution Needed"
    elif len(title_keywords) == 2:
        title = f"{title_keywords[0]} & {title_keywords[1]} Problem"
    else:
        title = f"{title_keywords[0]}, {title_keywords[1]} & {title_keywords[2]}"
    
    # Add context if we have category info
    categories = [a.get('product_category', '') for a in cluster if a.get('product_category')]
    if categories:
        most_common_category = Counter(categories).most_common(1)[0][0]
        if most_common_category and most_common_category != 'none':
            title = f"{title} - {most_common_category.replace('_', ' ').title()}"
    
    return title[:100]  # Limit to 100 chars


# ============================================================
# COMBINE AI SUMMARIES
# ============================================================

def combine_problem_summaries(cluster) -> str:
    """
    Combine AI-generated problem summaries from cluster into a comprehensive summary.
    
    Strategy:
    1. Collect unique problem summaries
    2. Identify common themes
    3. Create a combined narrative
    
    Args:
        cluster: List of analysis dictionaries with 'problem_summary' field
    
    Returns:
        Combined problem summary (max 1000 chars)
    """
    # Collect all unique summaries
    summaries = []
    seen_summaries = set()
    
    for analysis in cluster:
        summary = analysis.get('problem_summary', '').strip()
        if summary and summary.lower() not in seen_summaries:
            summaries.append(summary)
            seen_summaries.add(summary.lower())
    
    if not summaries:
        return "No problem summary available."
    
    if len(summaries) == 1:
        return summaries[0][:1000]
    
    # For multiple summaries, create a combined narrative
    # Start with the most detailed summary (longest)
    summaries.sort(key=len, reverse=True)
    primary_summary = summaries[0]
    
    # Extract key points from other summaries
    additional_points = []
    for summary in summaries[1:5]:  # Limit to top 5 summaries
        # Only add if it provides new information (not too similar to primary)
        if not _is_similar_text(summary, primary_summary):
            # Extract the core point (first sentence or key phrase)
            core_point = _extract_core_point(summary)
            if core_point and core_point not in additional_points:
                additional_points.append(core_point)
    
    # Combine into final summary
    if additional_points:
        combined = f"{primary_summary}\n\nRelated issues:\n"
        for i, point in enumerate(additional_points[:3], 1):  # Max 3 additional points
            combined += f"• {point}\n"
        return combined[:1000]
    
    return primary_summary[:1000]


def _is_similar_text(text1: str, text2: str, threshold: float = 0.5) -> bool:
    """Check if two texts are similar using word overlap"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return False
    
    overlap = len(words1 & words2)
    min_len = min(len(words1), len(words2))
    
    return (overlap / min_len) > threshold if min_len > 0 else False


def _extract_core_point(summary: str) -> str:
    """Extract the core point from a summary (first sentence or key phrase)"""
    # Split by sentence endings
    sentences = summary.replace('!', '.').replace('?', '.').split('.')
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20:  # Skip very short fragments
            return sentence
    
    # Fallback to first 100 chars
    return summary[:100].strip()


# ============================================================
# GET TOP POSTS BY ENGAGEMENT
# ============================================================

def get_top_posts_by_engagement(cluster, limit: int = 5) -> list:
    """
    Get the top N posts from a cluster sorted by engagement.
    
    Engagement = upvotes + (comments * 2)  # Comments weighted higher
    
    Args:
        cluster: List of analysis dictionaries with 'raw_posts' data
        limit: Maximum number of posts to return (default: 5)
    
    Returns:
        List of top analyses sorted by engagement (descending)
    """
    def get_engagement_score(analysis):
        """Calculate engagement score for an analysis"""
        # Try to get metrics from raw_posts relation
        raw_post = analysis.get('raw_posts', {})
        if isinstance(raw_post, dict):
            metrics = raw_post.get('metrics', {})
        else:
            metrics = {}
        
        # Also check if metrics are directly on analysis
        if not metrics:
            metrics = analysis.get('metrics', {})
        
        upvotes = metrics.get('upvotes', 0) or 0
        comments = metrics.get('comments', 0) or 0
        
        # Weight comments higher (they indicate deeper engagement)
        return upvotes + (comments * 2)
    
    # Sort by engagement score (descending)
    sorted_cluster = sorted(cluster, key=get_engagement_score, reverse=True)
    
    # Return top N
    return sorted_cluster[:limit]


# ============================================================
# CREATE OPPORTUNITY
# ============================================================

def create_opportunity_from_cluster(cluster):
    """
    Create an opportunity record from a cluster of analyses.
    
    Improvements:
    - Generate title from most common keywords
    - Combine AI summaries into problem_summary
    - Calculate proper confidence score
    """
    
    # Use highest pain severity
    max_pain = max(a.get('pain_severity', 5) for a in cluster)
    
    # Collect all keywords (for storage)
    all_keywords = []
    keyword_set = set()
    for a in cluster:
        for kw in a.get('keywords', []):
            if kw.lower() not in keyword_set:
                all_keywords.append(kw)
                keyword_set.add(kw.lower())
    
    # Generate title from most common keywords
    title = generate_title_from_keywords(cluster)
    
    # Combine AI summaries into comprehensive problem summary
    problem_summary = combine_problem_summaries(cluster)
    
    # Calculate confidence score
    # Formula: (pain_severity * 8) + (cluster_size * 4) + (keyword_diversity * 2)
    keyword_diversity = min(len(all_keywords), 10)  # Cap at 10
    confidence = min(100, (max_pain * 8) + (len(cluster) * 4) + (keyword_diversity * 2))
    
    # Determine category from most common
    categories = [a.get('product_category', 'none') for a in cluster if a.get('product_category')]
    category = Counter(categories).most_common(1)[0][0] if categories else 'none'
    
    # Determine growth pattern (basic heuristic for now)
    growth_pattern = 'regular'
    if len(cluster) >= 10:
        growth_pattern = 'growing'
    if len(cluster) >= 20 and max_pain >= 8:
        growth_pattern = 'exploding'
    
    # Calculate timing score based on recency and urgency
    timing_score = min(10, 5 + (max_pain - 5))  # Higher pain = more urgent
    
    # Create opportunity record
    opportunity = {
        'title': title,
        'problem_summary': problem_summary,
        'category': category,
        'keywords': all_keywords[:20],  # Store top 20 keywords
        'confidence_score': confidence,
        'pain_severity': max_pain,
        'growth_pattern': growth_pattern,
        'timing_score': timing_score,
        'mention_count': len(cluster),
        'detected_at': datetime.now().isoformat(),
        'status': 'active'
    }
    
    return opportunity, cluster


# ============================================================
# SAVE OPPORTUNITY WITH TOP 5 EVIDENCE
# ============================================================

def save_opportunity(opportunity, cluster):
    """
    Save opportunity and link TOP 5 evidence posts by engagement.
    
    Improvements:
    - Only links top 5 highest-engagement posts as evidence
    - Includes engagement score in weight calculation
    """
    
    # Insert opportunity
    result = supabase.table('opportunities').insert(opportunity).execute()
    
    if not result.data:
        print('✗ Failed to create opportunity')
        return None
    
    opp = result.data[0]
    print(f'✓ Created opportunity: {opp["title"][:50]}... (ID: {opp["id"]})')
    
    # Get TOP 5 posts by engagement
    top_posts = get_top_posts_by_engagement(cluster, limit=5)
    
    # Link evidence (only top 5 posts)
    evidence_records = []
    for i, analysis in enumerate(top_posts):
        # Calculate weight based on pain severity and rank
        pain = analysis.get('pain_severity', 5)
        rank_bonus = (5 - i) * 0.05  # Top post gets +0.25, 5th gets +0.05
        weight = min(1.0, (pain / 10.0) + rank_bonus)
        
        evidence_records.append({
            'opportunity_id': opp['id'],
            'raw_post_id': analysis['raw_post_id'],
            'signal_type': 'pain_point',
            'weight': round(weight, 2)
        })
    
    if evidence_records:
        supabase.table('evidence').insert(evidence_records).execute()
        print(f'  └─ Linked top {len(evidence_records)} evidence posts (by engagement)')
    
    return opp

def main():
    """Main opportunity creation function"""
    
    print('🎯 Creating opportunities from analyses...\n')
    
    # Get high-pain analyses
    analyses = get_high_pain_analyses()
    print(f'Found {len(analyses)} high-pain analyses (pain >= 7)')
    
    if not analyses:
        print('No analyses to process!')
        return
    
    # Cluster similar problems
    clusters = cluster_by_keywords(analyses)
    print(f'Grouped into {len(clusters)} opportunity clusters\n')
    
    # Create opportunities
    opportunities_created = 0
    
    for cluster in clusters:
        opportunity, cluster_posts = create_opportunity_from_cluster(cluster)
        
        # Only create if cluster has enough signal
        if len(cluster) >= 1:  # At least 1 post (for MVP, lower threshold)
            result = save_opportunity(opportunity, cluster_posts)
            if result:
                opportunities_created += 1
    
    print(f'\n✅ Complete! Created {opportunities_created} opportunities')


# ============================================================
# TEST FUNCTION
# ============================================================

def test_opportunity_creation():
    """
    Test the opportunity creation functions with sample data.
    Does NOT save to database - only tests the generation logic.
    """
    print("🧪 Testing Opportunity Creation...\n")
    
    # Sample cluster data (simulating post_analysis records)
    sample_cluster = [
        {
            'id': 'test_1',
            'raw_post_id': 'post_1',
            'problem_summary': 'Users are frustrated with pet medication tracking. They forget doses and struggle to maintain schedules.',
            'keywords': ['pet', 'medication', 'reminder', 'schedule', 'tracking', 'app'],
            'pain_severity': 8,
            'product_category': 'pet_care',
            'raw_posts': {
                'metrics': {'upvotes': 1500, 'comments': 234}
            }
        },
        {
            'id': 'test_2',
            'raw_post_id': 'post_2',
            'problem_summary': 'Managing multiple pets medications is a nightmare. Need a simple solution.',
            'keywords': ['pet', 'medication', 'management', 'multiple', 'reminder'],
            'pain_severity': 9,
            'product_category': 'pet_care',
            'raw_posts': {
                'metrics': {'upvotes': 890, 'comments': 156}
            }
        },
        {
            'id': 'test_3',
            'raw_post_id': 'post_3',
            'problem_summary': 'Vet appointments and medication schedules are impossible to coordinate.',
            'keywords': ['pet', 'vet', 'appointment', 'medication', 'schedule'],
            'pain_severity': 7,
            'product_category': 'pet_care',
            'raw_posts': {
                'metrics': {'upvotes': 456, 'comments': 89}
            }
        },
        {
            'id': 'test_4',
            'raw_post_id': 'post_4',
            'problem_summary': 'My elderly dog needs multiple medications daily. I keep missing doses.',
            'keywords': ['dog', 'medication', 'elderly', 'daily', 'doses'],
            'pain_severity': 8,
            'product_category': 'pet_care',
            'raw_posts': {
                'metrics': {'upvotes': 234, 'comments': 45}
            }
        },
        {
            'id': 'test_5',
            'raw_post_id': 'post_5',
            'problem_summary': 'Is there an app that reminds me to give my cat her pills?',
            'keywords': ['cat', 'medication', 'reminder', 'app', 'pills'],
            'pain_severity': 6,
            'product_category': 'pet_care',
            'raw_posts': {
                'metrics': {'upvotes': 123, 'comments': 34}
            }
        },
        {
            'id': 'test_6',
            'raw_post_id': 'post_6',
            'problem_summary': 'Would pay for a pet health tracking solution.',
            'keywords': ['pet', 'health', 'tracking', 'solution'],
            'pain_severity': 7,
            'product_category': 'pet_care',
            'raw_posts': {
                'metrics': {'upvotes': 567, 'comments': 78}
            }
        },
    ]
    
    print("=" * 60)
    print("1. TITLE GENERATION FROM KEYWORDS")
    print("=" * 60)
    
    title = generate_title_from_keywords(sample_cluster)
    print(f"\nGenerated Title: {title}")
    
    # Count keywords for visibility
    keyword_counts = Counter()
    for analysis in sample_cluster:
        for kw in analysis.get('keywords', []):
            keyword_counts[kw.lower()] += 1
    print(f"\nKeyword frequency: {keyword_counts.most_common(10)}")
    
    print("\n" + "=" * 60)
    print("2. COMBINE AI SUMMARIES")
    print("=" * 60)
    
    combined_summary = combine_problem_summaries(sample_cluster)
    print(f"\nCombined Summary:\n{combined_summary}")
    
    print("\n" + "=" * 60)
    print("3. TOP 5 POSTS BY ENGAGEMENT")
    print("=" * 60)
    
    top_posts = get_top_posts_by_engagement(sample_cluster, limit=5)
    print(f"\nTop {len(top_posts)} posts by engagement:")
    for i, post in enumerate(top_posts, 1):
        metrics = post.get('raw_posts', {}).get('metrics', {})
        upvotes = metrics.get('upvotes', 0)
        comments = metrics.get('comments', 0)
        engagement = upvotes + (comments * 2)
        print(f"  {i}. Post {post['raw_post_id']}: {upvotes} upvotes, {comments} comments (score: {engagement})")
    
    print("\n" + "=" * 60)
    print("4. CREATE OPPORTUNITY FROM CLUSTER")
    print("=" * 60)
    
    opportunity, _ = create_opportunity_from_cluster(sample_cluster)
    
    print(f"\nGenerated Opportunity:")
    print(f"  Title: {opportunity['title']}")
    print(f"  Category: {opportunity['category']}")
    print(f"  Confidence Score: {opportunity['confidence_score']}")
    print(f"  Pain Severity: {opportunity['pain_severity']}")
    print(f"  Growth Pattern: {opportunity['growth_pattern']}")
    print(f"  Timing Score: {opportunity['timing_score']}")
    print(f"  Mention Count: {opportunity['mention_count']}")
    print(f"  Keywords: {opportunity['keywords'][:10]}...")
    print(f"\n  Problem Summary:\n  {opportunity['problem_summary'][:300]}...")
    
    print("\n" + "=" * 60)
    print("5. TEST MULTIPLE CLUSTERS")
    print("=" * 60)
    
    # Create a second test cluster
    sample_cluster_2 = [
        {
            'id': 'test_7',
            'raw_post_id': 'post_7',
            'problem_summary': 'Smart home devices are unreliable and disconnected.',
            'keywords': ['smart', 'home', 'automation', 'unreliable', 'disconnect'],
            'pain_severity': 8,
            'product_category': 'smart_home',
            'raw_posts': {'metrics': {'upvotes': 2000, 'comments': 300}}
        },
        {
            'id': 'test_8',
            'raw_post_id': 'post_8',
            'problem_summary': 'Why cant smart home devices just work together?',
            'keywords': ['smart', 'home', 'integration', 'compatibility'],
            'pain_severity': 9,
            'product_category': 'smart_home',
            'raw_posts': {'metrics': {'upvotes': 1500, 'comments': 250}}
        },
    ]
    
    opp2, _ = create_opportunity_from_cluster(sample_cluster_2)
    
    print(f"\nCluster 2 Opportunity:")
    print(f"  Title: {opp2['title']}")
    print(f"  Confidence: {opp2['confidence_score']}")
    print(f"  Pain: {opp2['pain_severity']}")
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)
    
    return {
        'cluster_1': opportunity,
        'cluster_2': opp2,
        'top_posts_count': len(top_posts)
    }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_opportunity_creation()
    else:
        main()

