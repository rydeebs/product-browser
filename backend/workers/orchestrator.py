"""
Orchestrator to run the full pipeline: scrape -> analyze -> detect trends -> create opportunities
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scrapers.db_client import get_unprocessed_posts, mark_posts_processed
from workers.ai_analyzer import extract_opportunities_from_batch
from workers.nlp_processor import extract_keywords, extract_entities
from workers.trend_detector import cluster_opportunities, calculate_confidence_score
from workers.amazon_scraper import analyze_competitor_landscape
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

def run_full_pipeline(batch_size: int = 50):
    """
    Run the complete pipeline:
    1. Get unprocessed posts
    2. Analyze with AI
    3. Extract keywords and entities
    4. Cluster opportunities
    5. Calculate scores
    6. Save to database
    """
    print("Starting pipeline...")
    
    # Step 1: Get unprocessed posts
    print("Fetching unprocessed posts...")
    posts = get_unprocessed_posts(limit=batch_size)
    if not posts:
        print("No unprocessed posts found.")
        return
    
    print(f"Processing {len(posts)} posts...")
    
    # Step 2: AI Analysis
    print("Running AI analysis...")
    opportunities = extract_opportunities_from_batch(posts)
    
    # Step 3: NLP Processing
    print("Extracting keywords and entities...")
    for opp in opportunities:
        source_content = opp.get('source_content', '')
        opp['keywords'] = [kw[0] for kw in extract_keywords(source_content)]
        opp['entities'] = extract_entities(source_content)
    
    # Step 4: Cluster opportunities
    print("Clustering opportunities...")
    clusters = cluster_opportunities(opportunities)
    
    # Step 5: Calculate scores and save
    print("Calculating scores and saving...")
    for cluster in clusters:
        cluster_opps = cluster['opportunities']
        evidence_count = len(cluster_opps)
        
        # Create opportunity record
        representative = cluster['representative']
        opportunity = {
            'title': representative.get('analysis', '')[:200],  # Truncate
            'description': representative.get('analysis', ''),
            'keywords': representative.get('keywords', []),
            'confidence_score': calculate_confidence_score(representative, cluster_opps),
            'trend_score': evidence_count * 10,  # Simple trend score
            'evidence_count': evidence_count
        }
        
        # Save to opportunities table
        try:
            result = supabase.table('opportunities').insert(opportunity).execute()
            opportunity_id = result.data[0]['id'] if result.data else None
            
            # Link evidence
            if opportunity_id:
                for opp in cluster_opps:
                    supabase.table('evidence').insert({
                        'opportunity_id': opportunity_id,
                        'post_id': opp.get('post_id'),
                        'content': opp.get('source_content', '')
                    }).execute()
        except Exception as e:
            print(f"Error saving opportunity: {e}")
    
    # Step 6: Mark posts as processed
    post_ids = [post['id'] for post in posts]
    mark_posts_processed(post_ids)
    
    print(f"Pipeline complete! Processed {len(posts)} posts, created {len(clusters)} opportunities.")

if __name__ == '__main__':
    run_full_pipeline()

