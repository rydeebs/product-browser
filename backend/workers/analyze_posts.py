import os
import json
from datetime import datetime
from supabase import create_client, Client
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def get_unprocessed_posts(limit=50):
    """Get posts that haven't been analyzed yet"""
    result = supabase.table('raw_posts')\
        .select('*')\
        .eq('processed', False)\
        .limit(limit)\
        .execute()
    
    return result.data

def batch_analyze_posts(posts):
    """Analyze multiple posts with Claude in one API call"""
    
    if not posts:
        return []
    
    # Build batch prompt
    batch_text = ""
    for i, post in enumerate(posts, 1):
        upvotes = post['metrics'].get('upvotes', 0)
        comments = post['metrics'].get('comments', 0)
        batch_text += f"\nPost {i}:\n"
        batch_text += f"Content: {post['content']}\n"
        batch_text += f"Engagement: {upvotes} upvotes, {comments} comments\n"
    
    prompt = f"""Analyze these Reddit posts for product opportunity signals.



For each post, extract:

1. problem_summary: One sentence description of the core problem (or "none" if no problem)

2. pain_severity: Rate 1-10 how severe the problem is (0 if no problem)

3. willingness_to_pay: Does the post indicate willingness to pay? (true/false)

4. product_category: What type of solution? (new_invention | better_alternative | cheaper_option | quality_improvement | none)

5. keywords: 3-5 relevant keywords



Posts:

{batch_text}



Respond with ONLY a JSON array, no other text:

[

  {{"post_num": 1, "problem_summary": "...", "pain_severity": 8, "willingness_to_pay": true, "product_category": "better_alternative", "keywords": ["dog", "leash", "tangle"]}},

  ...

]

"""

    print(f'Sending {len(posts)} posts to Claude...')
    
    try:
        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = response.content[0].text
        
        # Extract JSON from response
        # Sometimes Claude wraps JSON in markdown code blocks
        if '```json' in response_text:
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            response_text = response_text[json_start:json_end]
        elif '```' in response_text:
            response_text = response_text.replace('```', '')
        
        analyses = json.loads(response_text)
        print(f'✓ Analyzed {len(analyses)} posts')
        return analyses
        
    except Exception as e:
        print(f'✗ Claude API error: {e}')
        return []

def save_analyses(posts, analyses):
    """Save analysis results to post_analysis table"""
    
    if not analyses:
        return 0
    
    records = []
    post_ids_to_mark = []
    
    for i, analysis in enumerate(analyses):
        if i >= len(posts):
            break
            
        post = posts[i]
        
        # Only save if there's actually a problem identified
        if analysis.get('pain_severity', 0) >= 5:
            records.append({
                'raw_post_id': post['id'],
                'problem_summary': analysis.get('problem_summary'),
                'pain_severity': analysis.get('pain_severity', 0),
                'willingness_to_pay': analysis.get('willingness_to_pay', False),
                'product_category': analysis.get('product_category', 'none'),
                'keywords': analysis.get('keywords', []),
                'analyzed_at': datetime.now().isoformat()
            })
        
        post_ids_to_mark.append(post['id'])
    
    # Save analyses
    if records:
        try:
            result = supabase.table('post_analysis').insert(records).execute()
            print(f'💾 Saved {len(records)} analyses to database')
        except Exception as e:
            print(f'✗ Database error: {e}')
    
    # Mark posts as processed
    try:
        supabase.table('raw_posts')\
            .update({'processed': True})\
            .in_('id', post_ids_to_mark)\
            .execute()
        print(f'✓ Marked {len(post_ids_to_mark)} posts as processed')
    except Exception as e:
        print(f'✗ Error marking posts: {e}')
    
    return len(records)

def main():
    """Main analysis function"""
    
    print('🔍 Starting post analysis...\n')
    
    # Get unprocessed posts
    posts = get_unprocessed_posts(limit=50)
    print(f'Found {len(posts)} unprocessed posts')
    
    if not posts:
        print('No posts to analyze!')
        return
    
    # Analyze in batches (50 posts per API call)
    analyses = batch_analyze_posts(posts)
    
    # Save results
    saved = save_analyses(posts, analyses)
    
    print(f'\n✅ Complete! {saved} high-quality analyses saved')
    print(f'Posts with pain_severity >= 5: {saved}')

if __name__ == '__main__':
    main()

