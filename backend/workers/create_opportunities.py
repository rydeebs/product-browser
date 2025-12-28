import os
from collections import defaultdict
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

def get_high_pain_analyses():
    """Get analyses with pain >= 7"""
    result = supabase.table('post_analysis')\
        .select('*, raw_posts(*)')\
        .gte('pain_severity', 7)\
        .execute()
    
    return result.data

def cluster_by_keywords(analyses):
    """Group similar problems by overlapping keywords"""
    clusters = []
    used = set()
    
    for i, analysis in enumerate(analyses):
        if i in used:
            continue
            
        cluster = [analysis]
        cluster_keywords = set(analysis['keywords'])
        used.add(i)
        
        # Find similar analyses
        for j, other in enumerate(analyses[i+1:], start=i+1):
            if j in used:
                continue
                
            other_keywords = set(other['keywords'])
            overlap = len(cluster_keywords & other_keywords)
            
            # If 2+ keywords match, group together
            if overlap >= 2:
                cluster.append(other)
                cluster_keywords.update(other_keywords)
                used.add(j)
        
        clusters.append(cluster)
    
    return clusters

def create_opportunity_from_cluster(cluster):
    """Create an opportunity record from a cluster of analyses"""
    
    # Use highest pain severity
    max_pain = max(a['pain_severity'] for a in cluster)
    
    # Combine keywords
    all_keywords = set()
    for a in cluster:
        all_keywords.update(a['keywords'])
    
    # Use first problem summary as title (or combine if needed)
    title = cluster[0]['problem_summary']
    
    # Calculate confidence score
    # Simple formula for now: (pain_severity * 10) + (cluster_size * 5)
    confidence = min(100, (max_pain * 10) + (len(cluster) * 5))
    
    # Determine category
    categories = [a.get('product_category', 'none') for a in cluster]
    category = max(set(categories), key=categories.count)
    
    # Create opportunity
    opportunity = {
        'title': title,
        'problem_summary': title,
        'category': category,
        'confidence_score': confidence,
        'pain_severity': max_pain,
        'growth_pattern': 'regular',  # Will calculate properly later
        'timing_score': 7,  # Default for now
        'detected_at': datetime.now().isoformat(),
        'status': 'active'
    }
    
    return opportunity, cluster

def save_opportunity(opportunity, cluster):
    """Save opportunity and link evidence"""
    
    # Insert opportunity
    result = supabase.table('opportunities').insert(opportunity).execute()
    
    if not result.data:
        print('✗ Failed to create opportunity')
        return None
    
    opp = result.data[0]
    print(f'✓ Created opportunity: {opp["title"][:50]}... (ID: {opp["id"]})')
    
    # Link evidence (post_analysis records)
    evidence_records = []
    for analysis in cluster:
        evidence_records.append({
            'opportunity_id': opp['id'],
            'raw_post_id': analysis['raw_post_id'],
            'signal_type': 'pain_point',
            'weight': analysis['pain_severity'] / 10.0
        })
    
    if evidence_records:
        supabase.table('evidence').insert(evidence_records).execute()
        print(f'  └─ Linked {len(evidence_records)} evidence posts')
    
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

if __name__ == '__main__':
    main()

