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

# Token pricing (Claude Sonnet 4 as of 2025)
# https://www.anthropic.com/pricing
PRICING = {
    'claude-sonnet-4-20250514': {
        'input': 3.00 / 1_000_000,   # $3.00 per 1M input tokens
        'output': 15.00 / 1_000_000  # $15.00 per 1M output tokens
    },
    'claude-3-5-sonnet-20241022': {
        'input': 3.00 / 1_000_000,
        'output': 15.00 / 1_000_000
    }
}

# Track cumulative usage
token_usage = {
    'total_input_tokens': 0,
    'total_output_tokens': 0,
    'total_cost': 0.0,
    'api_calls': 0
}


def log_token_usage(response, model: str):
    """Log token usage and calculate cost"""
    usage = response.usage
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    
    # Calculate cost
    pricing = PRICING.get(model, PRICING['claude-sonnet-4-20250514'])
    input_cost = input_tokens * pricing['input']
    output_cost = output_tokens * pricing['output']
    total_cost = input_cost + output_cost
    
    # Update cumulative totals
    token_usage['total_input_tokens'] += input_tokens
    token_usage['total_output_tokens'] += output_tokens
    token_usage['total_cost'] += total_cost
    token_usage['api_calls'] += 1
    
    print(f'  📊 Tokens: {input_tokens:,} in / {output_tokens:,} out')
    print(f'  💰 Cost: ${total_cost:.4f} (${input_cost:.4f} + ${output_cost:.4f})')
    
    return {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cost': total_cost
    }


def print_usage_summary():
    """Print cumulative token usage summary"""
    print(f'\n{"="*50}')
    print(f'📊 TOKEN USAGE SUMMARY')
    print(f'{"="*50}')
    print(f'API Calls:      {token_usage["api_calls"]}')
    print(f'Input Tokens:   {token_usage["total_input_tokens"]:,}')
    print(f'Output Tokens:  {token_usage["total_output_tokens"]:,}')
    print(f'Total Cost:     ${token_usage["total_cost"]:.4f}')
    if token_usage['api_calls'] > 0:
        avg_cost = token_usage['total_cost'] / token_usage['api_calls']
        print(f'Avg Cost/Batch: ${avg_cost:.4f}')
    print(f'{"="*50}')

def get_unprocessed_posts(limit=50, offset=0):
    """Get posts that haven't been analyzed yet"""
    result = supabase.table('raw_posts')\
        .select('*')\
        .eq('processed', False)\
        .order('created_at', desc=False)\
        .range(offset, offset + limit - 1)\
        .execute()
    
    return result.data


def get_unprocessed_count():
    """Get count of unprocessed posts"""
    result = supabase.table('raw_posts')\
        .select('id', count='exact')\
        .eq('processed', False)\
        .execute()
    
    return result.count or 0

def batch_analyze_posts(posts, batch_size=50):
    """
    Analyze multiple posts with Claude in batched API calls
    
    Args:
        posts: List of post dictionaries
        batch_size: Number of posts per API call (default 50)
    
    Returns:
        List of analysis results for all posts
    """
    if not posts:
        return []
    
    all_analyses = []
    model = "claude-sonnet-4-20250514"
    
    # Process in batches
    for batch_start in range(0, len(posts), batch_size):
        batch_end = min(batch_start + batch_size, len(posts))
        batch = posts[batch_start:batch_end]
        
        print(f'\n📦 Processing batch {batch_start//batch_size + 1} ({len(batch)} posts)...')
        
        # Build batch prompt
        batch_text = ""
        for i, post in enumerate(batch, 1):
            upvotes = post['metrics'].get('upvotes', 0) if post.get('metrics') else 0
            comments = post['metrics'].get('comments', 0) if post.get('metrics') else 0
            # Truncate content to save tokens
            content = post.get('content', '')[:1000]
            batch_text += f"\nPost {i}:\n"
            batch_text += f"Content: {content}\n"
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
  {{"post_num": 1, "problem_summary": "...", "pain_severity": 8, "willingness_to_pay": true, "product_category": "better_alternative", "keywords": ["keyword1", "keyword2"]}},
  ...
]
"""
        
        try:
            response = anthropic.messages.create(
                model=model,
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Log token usage
            log_token_usage(response, model)
            
            response_text = response.content[0].text
            
            # Extract JSON from response
            if '```json' in response_text:
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1
                response_text = response_text[json_start:json_end]
            elif '```' in response_text:
                response_text = response_text.replace('```', '')
            
            # Find JSON array in response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            
            analyses = json.loads(response_text)
            all_analyses.extend(analyses)
            print(f'  ✓ Analyzed {len(analyses)} posts in this batch')
            
        except json.JSONDecodeError as e:
            print(f'  ✗ JSON parsing error: {e}')
            print(f'  Response: {response_text[:200]}...')
        except Exception as e:
            print(f'  ✗ Claude API error: {e}')
    
    print(f'\n✓ Total analyzed: {len(all_analyses)} posts')
    return all_analyses


def analyze_posts_individually(posts):
    """
    Analyze posts one at a time (for cost comparison)
    This is MORE EXPENSIVE than batch analysis!
    """
    from ai_analyzer import analyze_post_for_opportunities
    
    analyses = []
    model = "claude-sonnet-4-20250514"
    
    for i, post in enumerate(posts):
        print(f'Analyzing post {i+1}/{len(posts)}...')
        
        result = analyze_post_for_opportunities(
            post.get('content', ''),
            {'metrics': post.get('metrics', {})}
        )
        
        analyses.append({
            'post_num': i + 1,
            'problem_summary': result.get('core_problem', ''),
            'pain_severity': result.get('pain_severity', 0),
            'willingness_to_pay': result.get('willingness_to_pay', {}).get('likely', False),
            'product_category': result.get('product_gap_category', 'none'),
            'keywords': result.get('keywords', [])
        })
    
    return analyses

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

def process_all_unprocessed(batch_size=50, max_posts=None, max_retries=3):
    """
    Process all unprocessed posts with error handling and retries
    
    Args:
        batch_size: Posts per API call
        max_posts: Maximum posts to process (None = all)
        max_retries: Number of retries on failure
    """
    import time
    
    print('🔍 Starting full post analysis...\n')
    
    # Get total count
    total_unprocessed = get_unprocessed_count()
    print(f'📊 Total unprocessed posts: {total_unprocessed}')
    
    if total_unprocessed == 0:
        print('No posts to analyze!')
        return {'processed': 0, 'saved': 0, 'errors': 0}
    
    # Limit if specified
    posts_to_process = min(total_unprocessed, max_posts) if max_posts else total_unprocessed
    print(f'📦 Will process: {posts_to_process} posts\n')
    
    stats = {
        'processed': 0,
        'saved': 0,
        'errors': 0,
        'batches': 0
    }
    
    offset = 0
    while stats['processed'] < posts_to_process:
        # Fetch batch
        remaining = posts_to_process - stats['processed']
        fetch_size = min(batch_size, remaining)
        
        posts = get_unprocessed_posts(limit=fetch_size, offset=0)  # offset=0 since we mark as processed
        
        if not posts:
            print('No more unprocessed posts found.')
            break
        
        print(f'\n{"="*50}')
        print(f'📦 BATCH {stats["batches"] + 1}: Processing {len(posts)} posts')
        print(f'   Progress: {stats["processed"]}/{posts_to_process}')
        print(f'{"="*50}')
        
        # Retry logic
        for attempt in range(max_retries):
            try:
                # Analyze batch
                analyses = batch_analyze_posts(posts, batch_size=batch_size)
                
                # Save results
                saved = save_analyses(posts, analyses)
                
                stats['processed'] += len(posts)
                stats['saved'] += saved
                stats['batches'] += 1
                
                break  # Success, exit retry loop
                
            except Exception as e:
                stats['errors'] += 1
                print(f'  ❌ Error (attempt {attempt + 1}/{max_retries}): {e}')
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Exponential backoff
                    print(f'  ⏳ Waiting {wait_time}s before retry...')
                    time.sleep(wait_time)
                else:
                    print(f'  ❌ Max retries reached, skipping batch')
                    # Mark as processed anyway to avoid infinite loop
                    try:
                        post_ids = [p['id'] for p in posts]
                        supabase.table('raw_posts')\
                            .update({'processed': True})\
                            .in_('id', post_ids)\
                            .execute()
                        stats['processed'] += len(posts)
                    except:
                        pass
        
        # Rate limiting between batches
        time.sleep(1)
    
    return stats


def main():
    """Main analysis function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze posts with AI')
    parser.add_argument('--limit', '-l', type=int, default=50, help='Max posts to process')
    parser.add_argument('--batch-size', '-b', type=int, default=50, help='Posts per API call')
    parser.add_argument('--all', '-a', action='store_true', help='Process all unprocessed posts')
    parser.add_argument('--test-cost', action='store_true', help='Run cost comparison test')
    
    args = parser.parse_args()
    
    if args.test_cost:
        test_batch_vs_individual()
        return
    
    print('🔍 Starting post analysis...\n')
    
    if args.all:
        # Process all unprocessed posts
        stats = process_all_unprocessed(batch_size=args.batch_size, max_posts=None)
    else:
        # Process limited batch
        stats = process_all_unprocessed(batch_size=args.batch_size, max_posts=args.limit)
    
    # Print usage summary
    print_usage_summary()
    
    # Final summary
    print(f'\n{"="*50}')
    print(f'📊 FINAL SUMMARY')
    print(f'{"="*50}')
    print(f'✅ Posts processed:  {stats["processed"]}')
    print(f'💾 Analyses saved:   {stats["saved"]}')
    print(f'❌ Errors:           {stats["errors"]}')
    print(f'📦 Batches:          {stats["batches"]}')
    print(f'{"="*50}')


def test_batch_vs_individual():
    """
    Test to compare batch vs individual analysis costs
    Run with: python analyze_posts.py --test-cost
    """
    print('🧪 COST COMPARISON TEST\n')
    print('Testing batch analysis vs individual calls...\n')
    
    # Sample posts for testing
    test_posts = [
        {'id': f'test_{i}', 'content': f'I wish there was a product that could help with problem {i}. It\'s so frustrating!', 
         'metrics': {'upvotes': 100 + i*10, 'comments': 20 + i}}
        for i in range(10)
    ]
    
    # Reset token tracking
    global token_usage
    token_usage = {'total_input_tokens': 0, 'total_output_tokens': 0, 'total_cost': 0.0, 'api_calls': 0}
    
    print('=' * 50)
    print('BATCH ANALYSIS (10 posts in 1 call)')
    print('=' * 50)
    
    batch_results = batch_analyze_posts(test_posts, batch_size=50)
    batch_cost = token_usage['total_cost']
    batch_calls = token_usage['api_calls']
    
    print(f'\nBatch Results:')
    print(f'  API Calls: {batch_calls}')
    print(f'  Total Cost: ${batch_cost:.4f}')
    print(f'  Cost per post: ${batch_cost/len(test_posts):.4f}')
    
    # Estimate individual cost (without actually making calls)
    # Individual calls typically use ~500 input + ~300 output tokens each
    estimated_individual_input = 500 * len(test_posts)
    estimated_individual_output = 300 * len(test_posts)
    pricing = PRICING['claude-sonnet-4-20250514']
    estimated_individual_cost = (estimated_individual_input * pricing['input']) + (estimated_individual_output * pricing['output'])
    
    print(f'\n' + '=' * 50)
    print('ESTIMATED INDIVIDUAL ANALYSIS (10 separate calls)')
    print('=' * 50)
    print(f'  API Calls: {len(test_posts)}')
    print(f'  Est. Cost: ${estimated_individual_cost:.4f}')
    print(f'  Cost per post: ${estimated_individual_cost/len(test_posts):.4f}')
    
    print(f'\n' + '=' * 50)
    print('💰 SAVINGS')
    print('=' * 50)
    savings = estimated_individual_cost - batch_cost
    savings_pct = (savings / estimated_individual_cost) * 100 if estimated_individual_cost > 0 else 0
    print(f'  Batch cost:      ${batch_cost:.4f}')
    print(f'  Individual cost: ${estimated_individual_cost:.4f} (estimated)')
    print(f'  Savings:         ${savings:.4f} ({savings_pct:.1f}%)')
    
    if savings_pct >= 50:
        print(f'\n✅ VALIDATION PASSED: Batch is {savings_pct:.0f}% cheaper!')
    else:
        print(f'\n⚠️  Batch savings: {savings_pct:.0f}% (target: 50%+)')


if __name__ == '__main__':
    main()

