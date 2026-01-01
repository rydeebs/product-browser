"""
Trend detection using clustering and scoring algorithms
Includes DBSCAN clustering, engagement baseline, and spike detection
"""
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import math
import numpy as np

# Try to import sklearn for DBSCAN
try:
    from sklearn.cluster import DBSCAN
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    print("Warning: scikit-learn not found. Using simple clustering.")
    HAS_SKLEARN = False

# Try to import supabase for database queries
try:
    from supabase import create_client
    from dotenv import load_dotenv
    load_dotenv()
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    HAS_SUPABASE = True
except:
    HAS_SUPABASE = False
    supabase = None


# ============================================================
# DBSCAN CLUSTERING
# ============================================================

def cluster_posts_dbscan(posts: list, min_cluster_size: int = 15, max_days: int = 7) -> list:
    """
    Cluster posts using DBSCAN algorithm based on keyword similarity
    
    Args:
        posts: List of post dictionaries with 'keywords' and 'content'
        min_cluster_size: Minimum posts to form a cluster (default: 15)
        max_days: Only include posts from last N days (default: 7)
    
    Returns:
        List of clusters with posts and metadata
    """
    if not HAS_SKLEARN:
        print("⚠️  sklearn not available, using simple clustering")
        return cluster_opportunities_simple(posts, min_cluster_size)
    
    if not posts:
        return []
    
    # Filter posts by date
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_days)
    recent_posts = []
    
    for post in posts:
        post_date = post.get('created_at') or post.get('scraped_at')
        if post_date:
            if isinstance(post_date, str):
                try:
                    post_date = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                except:
                    post_date = datetime.now(timezone.utc)
            if post_date.tzinfo is None:
                post_date = post_date.replace(tzinfo=timezone.utc)
            
            if post_date >= cutoff_date:
                recent_posts.append(post)
        else:
            recent_posts.append(post)  # Include if no date
    
    print(f"📅 Filtered to {len(recent_posts)} posts from last {max_days} days")
    
    if len(recent_posts) < min_cluster_size:
        print(f"⚠️  Not enough recent posts for clustering (need {min_cluster_size})")
        return []
    
    # Build text corpus from content and keywords
    texts = []
    for post in recent_posts:
        text_parts = []
        if post.get('content'):
            text_parts.append(post['content'][:500])
        if post.get('keywords'):
            text_parts.append(' '.join(post['keywords']))
        if post.get('problem_summary'):
            text_parts.append(post['problem_summary'])
        texts.append(' '.join(text_parts) if text_parts else '')
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(
        max_features=500,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError as e:
        print(f"⚠️  TF-IDF error: {e}")
        return cluster_opportunities_simple(recent_posts, min_cluster_size)
    
    # Run DBSCAN
    # eps: max distance between points in cluster
    # min_samples: minimum points to form a cluster
    dbscan = DBSCAN(
        eps=0.5,
        min_samples=max(3, min_cluster_size // 5),  # At least 3
        metric='cosine'
    )
    
    cluster_labels = dbscan.fit_predict(tfidf_matrix)
    
    # Group posts by cluster
    clusters_dict = defaultdict(list)
    for idx, label in enumerate(cluster_labels):
        if label != -1:  # -1 = noise (unclustered)
            clusters_dict[label].append(recent_posts[idx])
    
    # Filter clusters by minimum size
    clusters = []
    for cluster_id, cluster_posts in clusters_dict.items():
        if len(cluster_posts) >= min_cluster_size:
            # Find representative post (highest engagement)
            representative = max(
                cluster_posts,
                key=lambda p: (p.get('metrics', {}).get('upvotes', 0) + 
                              p.get('metrics', {}).get('comments', 0))
            )
            
            # Extract common keywords
            all_keywords = []
            for post in cluster_posts:
                all_keywords.extend(post.get('keywords', []))
            keyword_counts = defaultdict(int)
            for kw in all_keywords:
                keyword_counts[kw] += 1
            top_keywords = sorted(keyword_counts.items(), key=lambda x: -x[1])[:10]
            
            clusters.append({
                'cluster_id': cluster_id,
                'size': len(cluster_posts),
                'posts': cluster_posts,
                'representative': representative,
                'keywords': [kw for kw, _ in top_keywords],
                'total_engagement': sum(
                    p.get('metrics', {}).get('upvotes', 0) + 
                    p.get('metrics', {}).get('comments', 0)
                    for p in cluster_posts
                )
            })
    
    # Sort by size
    clusters.sort(key=lambda c: -c['size'])
    
    print(f"🎯 Found {len(clusters)} clusters with {min_cluster_size}+ posts")
    
    return clusters


def cluster_opportunities_simple(posts: list, min_cluster_size: int = 15) -> list:
    """
    Simple keyword-based clustering (fallback when sklearn not available)
    """
    # Group by primary keyword
    keyword_groups = defaultdict(list)
    
    for post in posts:
        keywords = post.get('keywords', [])
        if keywords:
            primary_keyword = keywords[0].lower()
            keyword_groups[primary_keyword].append(post)
    
    # Filter by minimum size
    clusters = []
    for keyword, group_posts in keyword_groups.items():
        if len(group_posts) >= min_cluster_size:
            clusters.append({
                'cluster_id': len(clusters),
                'size': len(group_posts),
                'posts': group_posts,
                'representative': group_posts[0],
                'keywords': [keyword],
                'total_engagement': sum(
                    p.get('metrics', {}).get('upvotes', 0) + 
                    p.get('metrics', {}).get('comments', 0)
                    for p in group_posts
                )
            })
    
    return sorted(clusters, key=lambda c: -c['size'])


# ============================================================
# ENGAGEMENT BASELINE & SPIKE DETECTION
# ============================================================

def calculate_engagement_baseline(category: str = None, days: int = 30) -> dict:
    """
    Calculate engagement baseline from historical data
    
    Args:
        category: Optional category filter
        days: Number of days to analyze (default: 30)
    
    Returns:
        Dict with mean, median, std of engagement
    """
    if not HAS_SUPABASE:
        print("⚠️  Supabase not available, using default baseline")
        return {'mean': 100, 'median': 50, 'std': 80, 'count': 0}
    
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    try:
        query = supabase.table('raw_posts')\
            .select('metrics')\
            .gte('scraped_at', cutoff_date)
        
        # Note: category filter would require a join with post_analysis
        result = query.execute()
        
        if not result.data:
            return {'mean': 100, 'median': 50, 'std': 80, 'count': 0}
        
        # Calculate engagement scores
        engagements = []
        for post in result.data:
            metrics = post.get('metrics', {})
            if isinstance(metrics, dict):
                engagement = metrics.get('upvotes', 0) + metrics.get('comments', 0)
                engagements.append(engagement)
        
        if not engagements:
            return {'mean': 100, 'median': 50, 'std': 80, 'count': 0}
        
        engagements = np.array(engagements)
        
        return {
            'mean': float(np.mean(engagements)),
            'median': float(np.median(engagements)),
            'std': float(np.std(engagements)),
            'count': len(engagements),
            'p75': float(np.percentile(engagements, 75)),
            'p90': float(np.percentile(engagements, 90))
        }
        
    except Exception as e:
        print(f"⚠️  Error calculating baseline: {e}")
        return {'mean': 100, 'median': 50, 'std': 80, 'count': 0}


def detect_engagement_spikes(posts: list, baseline: dict = None, spike_threshold: float = 2.0) -> list:
    """
    Detect posts with engagement significantly above baseline
    
    Args:
        posts: List of post dictionaries
        baseline: Engagement baseline dict (calculated if not provided)
        spike_threshold: Multiplier for spike detection (default: 2.0 = 200%)
    
    Returns:
        List of posts with engagement spikes
    """
    if baseline is None:
        baseline = calculate_engagement_baseline()
    
    baseline_mean = baseline.get('mean', 100)
    spike_level = baseline_mean * spike_threshold
    
    print(f"📊 Baseline engagement: {baseline_mean:.1f} (threshold: {spike_level:.1f})")
    
    spiking_posts = []
    
    for post in posts:
        metrics = post.get('metrics', {})
        engagement = metrics.get('upvotes', 0) + metrics.get('comments', 0)
        
        if engagement >= spike_level:
            spike_ratio = engagement / baseline_mean if baseline_mean > 0 else 0
            post['spike_ratio'] = spike_ratio
            post['engagement'] = engagement
            spiking_posts.append(post)
    
    # Sort by spike ratio
    spiking_posts.sort(key=lambda p: -p.get('spike_ratio', 0))
    
    print(f"🔥 Found {len(spiking_posts)} posts with {spike_threshold*100:.0f}%+ engagement")
    
    return spiking_posts


# ============================================================
# PAIN SEVERITY SCORING
# ============================================================

# Emotional intensity keywords for pain detection
EMOTION_KEYWORDS = {
    'high': ['hate', 'terrible', 'awful', 'worst', 'nightmare', 'disaster', 'impossible', 'unbearable'],
    'medium': ['frustrating', 'annoying', 'disappointed', 'struggle', 'difficult', 'problem', 'issue', 'broken'],
    'low': ['wish', 'want', 'need', 'looking for', 'hoping', 'would be nice', 'prefer']
}

# Willingness to pay indicators
WTP_KEYWORDS = [
    'would pay', 'take my money', 'shut up and take', 'worth paying',
    'pay for', 'buy', 'purchase', 'invest in', 'spend money',
    'how much', 'price', 'cost', 'budget', 'willing to pay',
    'subscription', 'premium', 'pro version'
]


def calculate_pain_severity(posts: list) -> dict:
    """
    Calculate pain severity score for a cluster of posts
    
    Weighting:
    - 40% AI-generated pain scores (1-10)
    - 30% Emotional intensity keywords
    - 30% Willingness-to-pay mentions
    
    Args:
        posts: List of post dictionaries with optional 'analysis' field
    
    Returns:
        Dict with pain_score (1-10), breakdown, and details
    """
    if not posts:
        return {'pain_score': 0, 'breakdown': {}, 'details': {}}
    
    # 1. Calculate AI pain score average (40%)
    ai_scores = []
    for post in posts:
        analysis = post.get('analysis', {})
        if isinstance(analysis, dict):
            pain = analysis.get('pain_severity')
            if pain is not None:
                try:
                    ai_scores.append(float(pain))
                except (ValueError, TypeError):
                    pass
    
    ai_score_avg = np.mean(ai_scores) if ai_scores else 5.0  # Default to 5
    ai_component = ai_score_avg * 0.4
    
    # 2. Calculate emotional intensity (30%)
    emotion_counts = {'high': 0, 'medium': 0, 'low': 0}
    total_posts = len(posts)
    
    for post in posts:
        content = (post.get('content', '') + ' ' + post.get('title', '')).lower()
        
        for level, keywords in EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content:
                    emotion_counts[level] += 1
                    break  # Count each post once per level
    
    # Weighted emotion score: high=10, medium=6, low=3
    emotion_score = (
        (emotion_counts['high'] / total_posts) * 10 +
        (emotion_counts['medium'] / total_posts) * 6 +
        (emotion_counts['low'] / total_posts) * 3
    )
    emotion_score = min(emotion_score, 10)  # Cap at 10
    emotion_component = emotion_score * 0.3
    
    # 3. Calculate willingness-to-pay (30%)
    wtp_count = 0
    wtp_posts = []
    
    for post in posts:
        content = (post.get('content', '') + ' ' + post.get('title', '')).lower()
        
        for keyword in WTP_KEYWORDS:
            if keyword in content:
                wtp_count += 1
                wtp_posts.append(post.get('id', 'unknown'))
                break  # Count each post once
    
    wtp_ratio = wtp_count / total_posts if total_posts > 0 else 0
    wtp_score = min(wtp_ratio * 20, 10)  # 50% WTP = score of 10
    wtp_component = wtp_score * 0.3
    
    # Final weighted score
    final_score = ai_component + emotion_component + wtp_component
    final_score = round(min(max(final_score, 1), 10), 2)  # Clamp 1-10
    
    return {
        'pain_score': final_score,
        'breakdown': {
            'ai_score': round(ai_score_avg, 2),
            'ai_component': round(ai_component, 2),
            'emotion_score': round(emotion_score, 2),
            'emotion_component': round(emotion_component, 2),
            'wtp_score': round(wtp_score, 2),
            'wtp_component': round(wtp_component, 2)
        },
        'details': {
            'posts_with_ai_score': len(ai_scores),
            'emotion_counts': emotion_counts,
            'wtp_count': wtp_count,
            'wtp_ratio': round(wtp_ratio * 100, 1),
            'total_posts': total_posts
        }
    }


# ============================================================
# GROWTH PATTERN CLASSIFICATION
# ============================================================

def classify_growth_pattern(posts: list = None, keyword: str = None, days: int = 90) -> dict:
    """
    Classify growth pattern based on post frequency over time
    
    Classifications:
    - 'exploding': >500% week-over-week growth
    - 'growing': 100-500% growth
    - 'regular': 0-100% growth (stable)
    - 'peaked': Declining (negative growth)
    
    Args:
        posts: List of posts with timestamps (optional if keyword provided)
        keyword: Keyword to query from database (optional)
        days: Number of days to analyze (default: 90)
    
    Returns:
        Dict with classification, growth_rate, and weekly_data
    """
    # Get posts either from argument or database
    if posts is None and keyword and HAS_SUPABASE:
        posts = _fetch_posts_for_keyword(keyword, days)
    
    if not posts:
        return {
            'classification': 'unknown',
            'growth_rate': 0,
            'weekly_data': [],
            'reason': 'No posts available'
        }
    
    # Group posts by week
    now = datetime.now(timezone.utc)
    weeks = defaultdict(int)
    
    for post in posts:
        post_date = post.get('created_at') or post.get('scraped_at')
        if post_date:
            if isinstance(post_date, str):
                try:
                    post_date = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                except:
                    continue
            if post_date.tzinfo is None:
                post_date = post_date.replace(tzinfo=timezone.utc)
            
            # Calculate week number (0 = current week, 1 = last week, etc.)
            days_ago = (now - post_date).days
            week_num = days_ago // 7
            if week_num < (days // 7):  # Only include weeks within range
                weeks[week_num] += 1
    
    if not weeks:
        return {
            'classification': 'unknown',
            'growth_rate': 0,
            'weekly_data': [],
            'reason': 'No dated posts'
        }
    
    # Calculate week-over-week growth rates
    max_week = max(weeks.keys())
    weekly_data = []
    growth_rates = []
    
    for week in range(max_week, -1, -1):  # Oldest to newest
        count = weeks.get(week, 0)
        weekly_data.append({
            'week': week,
            'weeks_ago': week,
            'count': count
        })
        
        # Calculate growth from previous week
        prev_count = weeks.get(week + 1, 0)
        if prev_count > 0:
            growth = ((count - prev_count) / prev_count) * 100
            growth_rates.append(growth)
            weekly_data[-1]['growth_rate'] = round(growth, 1)
    
    # Calculate average recent growth (last 4 weeks)
    recent_growth_rates = growth_rates[-4:] if len(growth_rates) >= 4 else growth_rates
    avg_growth = np.mean(recent_growth_rates) if recent_growth_rates else 0
    
    # Classify based on growth
    if avg_growth > 500:
        classification = 'exploding'
    elif avg_growth > 100:
        classification = 'growing'
    elif avg_growth >= 0:
        classification = 'regular'
    else:
        classification = 'peaked'
    
    # Additional context
    current_week_count = weeks.get(0, 0)
    last_week_count = weeks.get(1, 0)
    
    return {
        'classification': classification,
        'growth_rate': round(avg_growth, 1),
        'weekly_data': weekly_data,
        'current_week_posts': current_week_count,
        'last_week_posts': last_week_count,
        'total_posts': len(posts),
        'weeks_analyzed': len(weeks)
    }


def _fetch_posts_for_keyword(keyword: str, days: int = 90) -> list:
    """Fetch posts containing a keyword from database"""
    if not HAS_SUPABASE:
        return []
    
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    try:
        result = supabase.table('raw_posts')\
            .select('id, content, title, scraped_at, metrics')\
            .gte('scraped_at', cutoff_date)\
            .ilike('content', f'%{keyword}%')\
            .execute()
        
        return result.data or []
    except Exception as e:
        print(f"⚠️  Error fetching posts: {e}")
        return []


def filter_peaked_trends(clusters: list) -> list:
    """
    Filter out clusters with 'peaked' growth pattern
    
    Args:
        clusters: List of cluster dictionaries
    
    Returns:
        Filtered list excluding peaked trends
    """
    filtered = []
    peaked_count = 0
    
    for cluster in clusters:
        posts = cluster.get('posts', [])
        growth_info = classify_growth_pattern(posts)
        
        cluster['growth_pattern'] = growth_info
        
        if growth_info['classification'] != 'peaked':
            filtered.append(cluster)
        else:
            peaked_count += 1
            print(f"📉 Filtered out peaked cluster: {cluster.get('keywords', ['unknown'])[:3]} "
                  f"(growth: {growth_info['growth_rate']}%)")
    
    print(f"🔍 Filtered {peaked_count} peaked trends, {len(filtered)} remaining")
    
    return filtered


def score_cluster(cluster: dict) -> dict:
    """
    Calculate comprehensive score for a cluster
    
    Combines:
    - Pain severity
    - Growth pattern
    - Engagement metrics
    
    Args:
        cluster: Cluster dictionary with posts
    
    Returns:
        Cluster with added scores
    """
    posts = cluster.get('posts', [])
    
    # Calculate pain severity
    pain_info = calculate_pain_severity(posts)
    cluster['pain_severity'] = pain_info['pain_score']
    cluster['pain_details'] = pain_info
    
    # Calculate growth pattern
    growth_info = classify_growth_pattern(posts)
    cluster['growth_pattern'] = growth_info['classification']
    cluster['growth_rate'] = growth_info['growth_rate']
    cluster['growth_details'] = growth_info
    
    # Calculate overall opportunity score
    # Weight: 40% pain, 30% growth, 30% engagement
    pain_component = pain_info['pain_score'] * 0.4
    
    # Growth score (exploding=10, growing=7, regular=4, peaked=1)
    growth_scores = {'exploding': 10, 'growing': 7, 'regular': 4, 'peaked': 1, 'unknown': 3}
    growth_score = growth_scores.get(growth_info['classification'], 3)
    growth_component = growth_score * 0.3
    
    # Engagement score (normalize to 1-10)
    total_engagement = cluster.get('total_engagement', 0)
    engagement_score = min(10, max(1, math.log10(total_engagement + 1) * 2))
    engagement_component = engagement_score * 0.3
    
    cluster['opportunity_score'] = round(pain_component + growth_component + engagement_component, 2)
    
    return cluster


# ============================================================
# CONFIDENCE SCORING (0-100 scale)
# ============================================================

# DIY attempt indicators
DIY_KEYWORDS = [
    'tried to make', 'built my own', 'diy', 'homemade', 'made myself',
    'hacked together', 'workaround', 'jury-rigged', 'makeshift',
    'cobbled together', 'rigged up', 'custom solution', 'self-made'
]

# Minimum confidence threshold for creating opportunities
CONFIDENCE_THRESHOLD = 60


def calculate_cluster_confidence(cluster: dict, search_volume: int = None) -> dict:
    """
    Calculate confidence score (0-100) for a cluster based on spec.
    
    Signal weights:
    - High signals (3 points each): max_engagement>1000, search_volume>5000, 
      pain_severity>=8, growth_pattern=='exploding'
    - Medium signals (2 points each): mention_count>=50, willingness_to_pay, diy_attempts
    - Low signals (1 point each): low_competition
    
    Max points: (4 * 3) + (3 * 2) + 1 = 19
    
    Args:
        cluster: Cluster dict with posts, pain_severity, growth_pattern
        search_volume: Optional search volume from Google Trends
    
    Returns:
        Dict with confidence_score (0-100) and signal breakdown
    """
    posts = cluster.get('posts', [])
    
    # Calculate metrics if not already present
    if 'pain_severity' not in cluster:
        pain_info = calculate_pain_severity(posts)
        cluster['pain_severity'] = pain_info['pain_score']
        cluster['pain_details'] = pain_info
    
    if 'growth_pattern' not in cluster:
        growth_info = classify_growth_pattern(posts)
        cluster['growth_pattern'] = growth_info['classification']
    
    # ============================================================
    # HIGH SIGNALS (3 points each)
    # ============================================================
    high_signals = 0
    high_signal_details = []
    
    # 1. Max engagement > 1000
    max_engagement = 0
    for post in posts:
        metrics = post.get('metrics', {})
        engagement = metrics.get('upvotes', 0) + metrics.get('comments', 0)
        max_engagement = max(max_engagement, engagement)
    
    if max_engagement > 1000:
        high_signals += 1
        high_signal_details.append(f'max_engagement={max_engagement}')
    
    # 2. Search volume > 5000
    if search_volume and search_volume > 5000:
        high_signals += 1
        high_signal_details.append(f'search_volume={search_volume}')
    
    # 3. Pain severity >= 8
    pain_severity = cluster.get('pain_severity', 0)
    if pain_severity >= 8:
        high_signals += 1
        high_signal_details.append(f'pain_severity={pain_severity:.1f}')
    
    # 4. Growth pattern == 'exploding'
    growth_pattern = cluster.get('growth_pattern', 'unknown')
    if growth_pattern == 'exploding':
        high_signals += 1
        high_signal_details.append(f'growth_pattern={growth_pattern}')
    
    # ============================================================
    # MEDIUM SIGNALS (2 points each)
    # ============================================================
    medium_signals = 0
    medium_signal_details = []
    
    # 1. Mention count >= 50
    mention_count = len(posts)
    if mention_count >= 50:
        medium_signals += 1
        medium_signal_details.append(f'mention_count={mention_count}')
    
    # 2. Willingness to pay detected
    wtp_count = 0
    for post in posts:
        content = (post.get('content', '') + ' ' + post.get('title', '')).lower()
        for keyword in WTP_KEYWORDS:
            if keyword in content:
                wtp_count += 1
                break
    
    willingness_to_pay = wtp_count >= (len(posts) * 0.1)  # At least 10% mention WTP
    if willingness_to_pay:
        medium_signals += 1
        medium_signal_details.append(f'wtp_ratio={wtp_count}/{len(posts)}')
    
    # 3. DIY attempts detected
    diy_count = 0
    for post in posts:
        content = (post.get('content', '') + ' ' + post.get('title', '')).lower()
        for keyword in DIY_KEYWORDS:
            if keyword in content:
                diy_count += 1
                break
    
    diy_attempts = diy_count >= 3  # At least 3 DIY mentions
    if diy_attempts:
        medium_signals += 1
        medium_signal_details.append(f'diy_attempts={diy_count}')
    
    # ============================================================
    # LOW SIGNALS (1 point each)
    # ============================================================
    low_signals = 0
    low_signal_details = []
    
    # 1. Low competition (placeholder - would need competitor data)
    # For now, assume low competition if cluster is niche (smaller size)
    low_competition = mention_count < 100 and pain_severity >= 6
    if low_competition:
        low_signals += 1
        low_signal_details.append('low_competition=inferred')
    
    # ============================================================
    # CALCULATE FINAL SCORE
    # ============================================================
    total_points = (high_signals * 3) + (medium_signals * 2) + low_signals
    max_points = (4 * 3) + (3 * 2) + 1  # 19 max
    
    confidence_score = round((total_points / max_points) * 100)
    
    return {
        'confidence_score': confidence_score,
        'total_points': total_points,
        'max_points': max_points,
        'meets_threshold': confidence_score >= CONFIDENCE_THRESHOLD,
        'signals': {
            'high': {
                'count': high_signals,
                'max': 4,
                'points': high_signals * 3,
                'details': high_signal_details
            },
            'medium': {
                'count': medium_signals,
                'max': 3,
                'points': medium_signals * 2,
                'details': medium_signal_details
            },
            'low': {
                'count': low_signals,
                'max': 1,
                'points': low_signals,
                'details': low_signal_details
            }
        },
        'metrics': {
            'max_engagement': max_engagement,
            'mention_count': mention_count,
            'pain_severity': pain_severity,
            'growth_pattern': growth_pattern,
            'wtp_count': wtp_count,
            'diy_count': diy_count
        }
    }


def filter_by_confidence(clusters: list, threshold: int = CONFIDENCE_THRESHOLD) -> tuple:
    """
    Filter clusters by confidence score threshold.
    Only create opportunities if score > threshold.
    
    Args:
        clusters: List of cluster dicts
        threshold: Minimum confidence score (default: 60)
    
    Returns:
        Tuple of (passing_clusters, filtered_clusters)
    """
    passing = []
    filtered = []
    
    for cluster in clusters:
        confidence = calculate_cluster_confidence(cluster)
        cluster['confidence'] = confidence
        cluster['confidence_score'] = confidence['confidence_score']
        
        if confidence['confidence_score'] >= threshold:
            passing.append(cluster)
        else:
            filtered.append(cluster)
    
    print(f"✅ {len(passing)} clusters passed confidence threshold ({threshold})")
    print(f"❌ {len(filtered)} clusters filtered out")
    
    return passing, filtered


# ============================================================
# ORIGINAL FUNCTIONS (maintained for compatibility)
# ============================================================

def cluster_opportunities(opportunities: list, similarity_threshold: float = 0.7) -> list:
    """
    Cluster similar opportunities together (original simple method)
    
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
    Calculate similarity between two opportunities (Jaccard similarity)
    """
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
    """
    base_score = 50.0
    
    # Increase score based on number of evidence
    evidence_bonus = min(len(evidence) * 5, 30)
    
    # Increase score based on recency
    recent_evidence = 0
    for e in evidence:
        created_at = e.get('created_at')
        if created_at:
            try:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if created_at > datetime.now(timezone.utc) - timedelta(days=7):
                    recent_evidence += 1
            except:
                pass
    
    recency_bonus = min(recent_evidence * 3, 20)
    
    return min(base_score + evidence_bonus + recency_bonus, 100.0)


def calculate_trend_score(opportunity: dict, time_window_days: int = 30) -> float:
    """
    Calculate trend score based on frequency over time
    """
    return opportunity.get('mention_count', 0) * 10


# ============================================================
# TEST FUNCTION
# ============================================================

def test_trend_detector():
    """Test the trend detector with sample data"""
    print("🧪 Testing Trend Detector...\n")
    
    # Generate sample posts - 100 posts designed to form 3-5 clusters
    sample_posts = []
    
    # 5 distinct topic clusters with varying emotional intensity and WTP
    topic_clusters = [
        {
            'keywords': ['water', 'bottle', 'hydration', 'tracking', 'smart'],
            'content_template': 'I need a water bottle that tracks my hydration. {variation}',
            'pain_variations': [
                'I hate that nothing tracks properly!',
                'So frustrating when I forget to drink water.',
                'Would pay good money for something that actually works.',
                'Terrible options on the market right now.',
                'I wish someone would make a smart bottle.'
            ]
        },
        {
            'keywords': ['pet', 'medication', 'reminder', 'app', 'schedule'],
            'content_template': 'Looking for a pet medication reminder app. {variation}',
            'pain_variations': [
                'This is a nightmare to manage!',
                'Shut up and take my money if someone builds this.',
                'Struggling to keep track of my dogs meds.',
                'Would definitely pay for a subscription.',
                'Why doesnt this exist yet?'
            ]
        },
        {
            'keywords': ['cable', 'management', 'desk', 'organization', 'tidy'],
            'content_template': 'My desk cables are a mess. {variation}',
            'pain_variations': [
                'This is really annoying.',
                'Looking for a better solution.',
                'Anyone have recommendations?',
                'Need something to organize wires.',
                'Hoping to find a good product.'
            ]
        },
        {
            'keywords': ['meal', 'prep', 'container', 'food', 'portion'],
            'content_template': 'Need better meal prep containers. {variation}',
            'pain_variations': [
                'Current ones are terrible quality.',
                'Frustrated with lids that dont seal.',
                'Would buy premium containers if they lasted.',
                'The worst part is finding matching lids.',
                'Hate when they stain from tomato sauce.'
            ]
        },
        {
            'keywords': ['back', 'pain', 'ergonomic', 'chair', 'posture'],
            'content_template': 'Suffering from back pain at my desk. {variation}',
            'pain_variations': [
                'This is unbearable after 8 hours!',
                'Would invest in anything that helps.',
                'Impossible to find a good chair under $500.',
                'My posture is a disaster.',
                'Take my money for something that works!'
            ]
        },
    ]
    
    # Generate posts with varying dates to test growth patterns
    # Cluster 0: Exploding (more posts recently) - HIGH QUALITY
    # Cluster 1: Growing (moderate increase) - MEDIUM QUALITY
    # Cluster 2: Regular (stable) - LOW QUALITY
    # Cluster 3: Peaked (declining) - WILL BE FILTERED
    # Cluster 4: Growing - MEDIUM QUALITY
    
    growth_patterns = {
        0: [0, 0, 0, 1, 1, 2, 3, 5, 7, 10, 15, 20, 25, 30],  # Exploding
        1: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],  # Growing
        2: [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],  # Regular
        3: [20, 18, 15, 12, 10, 8, 6, 5, 4, 3, 2, 2, 1, 1],  # Peaked (declining)
        4: [3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26],  # Growing
    }
    
    # Engagement levels per cluster (to test high engagement signal)
    engagement_multipliers = {
        0: 50,   # High engagement (will have some >1000)
        1: 20,   # Medium engagement
        2: 5,    # Low engagement
        3: 15,   # Medium engagement
        4: 25,   # Medium-high engagement
    }
    
    # Pain score ranges per cluster
    pain_score_ranges = {
        0: (8, 10),   # High pain (>=8 for high signal)
        1: (6, 8),    # Medium pain
        2: (3, 5),    # Low pain
        3: (5, 7),    # Medium pain
        4: (7, 9),    # Medium-high pain
    }
    
    post_id = 0
    for cluster_idx in range(5):
        topic = topic_clusters[cluster_idx]
        pattern = growth_patterns[cluster_idx]
        engagement_mult = engagement_multipliers[cluster_idx]
        pain_min, pain_max = pain_score_ranges[cluster_idx]
        
        # Generate posts according to growth pattern
        for week_idx, count in enumerate(pattern):
            for _ in range(count):
                variation = topic['pain_variations'][post_id % len(topic['pain_variations'])]
                days_ago = week_idx * 7 + (post_id % 7)  # Spread within week
                
                # Calculate engagement (some posts will exceed 1000)
                base_engagement = 50 + (post_id * engagement_mult) % (500 * engagement_mult // 10)
                
                sample_posts.append({
                    'id': f'test_{post_id}',
                    'content': topic['content_template'].format(variation=variation),
                    'keywords': topic['keywords'],
                    'problem_summary': f'Problem related to {topic["keywords"][0]}',
                    'metrics': {
                        'upvotes': base_engagement,
                        'comments': base_engagement // 5
                    },
                    'created_at': (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(),
                    'analysis': {
                        'pain_severity': pain_min + (post_id % (pain_max - pain_min + 1))
                    }
                })
                post_id += 1
    
    print(f"Generated {len(sample_posts)} sample posts\n")
    
    print("=" * 60)
    print("1. DBSCAN CLUSTERING")
    print("=" * 60)
    
    clusters = cluster_posts_dbscan(sample_posts, min_cluster_size=5, max_days=90)
    
    print(f"\nFound {len(clusters)} clusters:")
    for cluster in clusters[:5]:
        print(f"  - Cluster {cluster['cluster_id']}: {cluster['size']} posts")
        print(f"    Keywords: {cluster['keywords'][:5]}")
        print(f"    Total engagement: {cluster['total_engagement']}")
    
    print("\n" + "=" * 60)
    print("2. PAIN SEVERITY SCORING")
    print("=" * 60)
    
    for cluster in clusters[:3]:
        pain_result = calculate_pain_severity(cluster['posts'])
        print(f"\nCluster '{cluster['keywords'][0]}':")
        print(f"  Pain Score: {pain_result['pain_score']}/10")
        print(f"  Breakdown:")
        print(f"    - AI Score: {pain_result['breakdown']['ai_score']:.1f} (40% weight)")
        print(f"    - Emotion Score: {pain_result['breakdown']['emotion_score']:.1f} (30% weight)")
        print(f"    - WTP Score: {pain_result['breakdown']['wtp_score']:.1f} (30% weight)")
        print(f"  Details:")
        print(f"    - Emotion counts: {pain_result['details']['emotion_counts']}")
        print(f"    - WTP ratio: {pain_result['details']['wtp_ratio']}%")
    
    print("\n" + "=" * 60)
    print("3. GROWTH PATTERN CLASSIFICATION")
    print("=" * 60)
    
    for cluster in clusters:
        growth_result = classify_growth_pattern(cluster['posts'])
        print(f"\nCluster '{cluster['keywords'][0]}':")
        print(f"  Classification: {growth_result['classification'].upper()}")
        print(f"  Growth Rate: {growth_result['growth_rate']}% week-over-week")
        print(f"  Current week: {growth_result['current_week_posts']} posts")
        print(f"  Last week: {growth_result['last_week_posts']} posts")
    
    print("\n" + "=" * 60)
    print("4. FILTER PEAKED TRENDS")
    print("=" * 60)
    
    active_clusters = filter_peaked_trends(clusters)
    print(f"\nActive clusters (non-peaked): {len(active_clusters)}")
    
    print("\n" + "=" * 60)
    print("5. COMPREHENSIVE CLUSTER SCORING")
    print("=" * 60)
    
    scored_clusters = [score_cluster(c) for c in active_clusters]
    scored_clusters.sort(key=lambda c: -c['opportunity_score'])
    
    print("\nTop opportunities by score:")
    for i, cluster in enumerate(scored_clusters[:5], 1):
        print(f"\n{i}. {cluster['keywords'][0].title()}")
        print(f"   Opportunity Score: {cluster['opportunity_score']}/10")
        print(f"   Pain Severity: {cluster['pain_severity']}/10")
        print(f"   Growth Pattern: {cluster['growth_pattern']} ({cluster['growth_rate']}%)")
        print(f"   Posts: {cluster['size']}")
    
    print("\n" + "=" * 60)
    print("6. CONFIDENCE SCORING (0-100)")
    print("=" * 60)
    
    print(f"\nConfidence threshold: {CONFIDENCE_THRESHOLD}")
    
    # Create a high-quality test cluster to demonstrate passing threshold
    print("\n--- Testing with HIGH-QUALITY synthetic cluster ---")
    high_quality_cluster = {
        'keywords': ['smart', 'home', 'automation', 'device'],
        'size': 75,
        'total_engagement': 50000,
        'posts': [
            {
                'id': f'hq_{i}',
                'content': 'I hate that smart home devices are so unreliable! Would pay premium for something that actually works. I tried to make my own DIY solution but failed.',
                'title': 'Smart home frustration',
                'metrics': {'upvotes': 1500 if i < 5 else 200, 'comments': 300 if i < 5 else 50},
                'created_at': (datetime.now(timezone.utc) - timedelta(days=i % 7)).isoformat(),
                'analysis': {'pain_severity': 9}
            }
            for i in range(75)
        ],
        'pain_severity': 9.2,
        'growth_pattern': 'exploding',
        'growth_rate': 650
    }
    
    hq_confidence = calculate_cluster_confidence(high_quality_cluster, search_volume=8000)
    print(f"\nHigh-Quality Cluster: {'✅ PASS' if hq_confidence['meets_threshold'] else '❌ FAIL'}")
    print(f"  Confidence Score: {hq_confidence['confidence_score']}/100")
    print(f"  Total Points: {hq_confidence['total_points']}/{hq_confidence['max_points']}")
    print(f"  High Signals: {hq_confidence['signals']['high']['count']}/4 ({hq_confidence['signals']['high']['points']} pts)")
    if hq_confidence['signals']['high']['details']:
        print(f"    → {', '.join(hq_confidence['signals']['high']['details'])}")
    print(f"  Medium Signals: {hq_confidence['signals']['medium']['count']}/3 ({hq_confidence['signals']['medium']['points']} pts)")
    if hq_confidence['signals']['medium']['details']:
        print(f"    → {', '.join(hq_confidence['signals']['medium']['details'])}")
    print(f"  Low Signals: {hq_confidence['signals']['low']['count']}/1 ({hq_confidence['signals']['low']['points']} pts)")
    if hq_confidence['signals']['low']['details']:
        print(f"    → {', '.join(hq_confidence['signals']['low']['details'])}")
    
    # Create a medium-quality cluster
    print("\n--- Testing with MEDIUM-QUALITY synthetic cluster ---")
    medium_quality_cluster = {
        'keywords': ['fitness', 'tracker', 'app'],
        'size': 55,
        'total_engagement': 15000,
        'posts': [
            {
                'id': f'mq_{i}',
                'content': 'Looking for a better fitness tracker. Current one is frustrating.',
                'title': 'Fitness tracker search',
                'metrics': {'upvotes': 300, 'comments': 50},
                'created_at': (datetime.now(timezone.utc) - timedelta(days=i % 14)).isoformat(),
                'analysis': {'pain_severity': 6}
            }
            for i in range(55)
        ],
        'pain_severity': 6.0,
        'growth_pattern': 'growing',
        'growth_rate': 150
    }
    
    mq_confidence = calculate_cluster_confidence(medium_quality_cluster, search_volume=4000)
    print(f"\nMedium-Quality Cluster: {'✅ PASS' if mq_confidence['meets_threshold'] else '❌ FAIL'}")
    print(f"  Confidence Score: {mq_confidence['confidence_score']}/100")
    print(f"  Total Points: {mq_confidence['total_points']}/{mq_confidence['max_points']}")
    print(f"  High Signals: {mq_confidence['signals']['high']['count']}/4")
    print(f"  Medium Signals: {mq_confidence['signals']['medium']['count']}/3")
    print(f"  Low Signals: {mq_confidence['signals']['low']['count']}/1")
    
    print("\n--- Testing with actual scraped clusters ---")
    print("\nCalculating confidence for scored clusters:")
    
    for cluster in scored_clusters:
        confidence = calculate_cluster_confidence(cluster, search_volume=3000)  # Sample search volume
        cluster['confidence'] = confidence
        
        status = "✅ PASS" if confidence['meets_threshold'] else "❌ FAIL"
        print(f"\n{cluster['keywords'][0].title()} - {status}")
        print(f"  Confidence Score: {confidence['confidence_score']}/100")
        print(f"  Total Points: {confidence['total_points']}/{confidence['max_points']}")
        print(f"  High Signals: {confidence['signals']['high']['count']}/4 ({confidence['signals']['high']['points']} pts)")
        if confidence['signals']['high']['details']:
            print(f"    → {', '.join(confidence['signals']['high']['details'])}")
        print(f"  Medium Signals: {confidence['signals']['medium']['count']}/3 ({confidence['signals']['medium']['points']} pts)")
        if confidence['signals']['medium']['details']:
            print(f"    → {', '.join(confidence['signals']['medium']['details'])}")
        print(f"  Low Signals: {confidence['signals']['low']['count']}/1 ({confidence['signals']['low']['points']} pts)")
        if confidence['signals']['low']['details']:
            print(f"    → {', '.join(confidence['signals']['low']['details'])}")
    
    print("\n" + "=" * 60)
    print("7. FILTER BY CONFIDENCE THRESHOLD")
    print("=" * 60)
    
    passing_clusters, filtered_clusters = filter_by_confidence(scored_clusters, threshold=CONFIDENCE_THRESHOLD)
    
    print(f"\nPassing clusters (score >= {CONFIDENCE_THRESHOLD}):")
    for cluster in passing_clusters:
        print(f"  ✅ {cluster['keywords'][0].title()}: {cluster['confidence_score']}/100")
    
    print(f"\nFiltered clusters (score < {CONFIDENCE_THRESHOLD}):")
    for cluster in filtered_clusters:
        print(f"  ❌ {cluster['keywords'][0].title()}: {cluster['confidence_score']}/100")
    
    print("\n" + "=" * 60)
    print("8. ENGAGEMENT BASELINE (from database)")
    print("=" * 60)
    
    baseline = calculate_engagement_baseline(days=30)
    print(f"\nBaseline stats:")
    print(f"  Mean: {baseline['mean']:.1f}")
    print(f"  Median: {baseline.get('median', 'N/A')}")
    print(f"  Std: {baseline.get('std', 'N/A')}")
    print(f"  Count: {baseline['count']}")
    
    print("\n" + "=" * 60)
    print("✅ Trend Detector test complete!")
    print("=" * 60)
    
    # Summary
    print("\n📊 SUMMARY:")
    print(f"  Total clusters found: {len(clusters)}")
    print(f"  Active (non-peaked): {len(active_clusters)}")
    print(f"  Passing confidence: {len(passing_clusters)}")
    print(f"  Ready for opportunities: {len(passing_clusters)}")
    
    return {
        'clusters': len(clusters),
        'active_clusters': len(active_clusters),
        'scored_clusters': len(scored_clusters),
        'passing_clusters': len(passing_clusters),
        'filtered_clusters': len(filtered_clusters),
        'baseline': baseline
    }


if __name__ == '__main__':
    test_trend_detector()

