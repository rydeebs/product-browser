import os
import sys
import json
import time
import hashlib
import argparse
import requests
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Pain detection patterns - posts matching these are high-value
PAIN_PATTERNS = [
    "is there a product that",
    "i wish someone made",
    "i wish there was",
    "why doesn't",
    "why isn't there",
    "frustrated with",
    "hate that",
    "need a better",
    "looking for something",
    "can't find a",
    "does anyone know",
    "any recommendations for",
    "sick of",
    "tired of",
    "annoying that",
    "would pay for",
    "shut up and take my money",
    "someone should make",
    "why hasn't anyone",
    "there should be",
]

def load_subreddits_config():
    """Load subreddits from config file"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'subreddits.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  Config file not found, using defaults")
        return {
            "general": ["shutupandtakemymoney", "DidntKnowIWantedThat"],
            "home": ["HomeImprovement"],
            "pets": ["dogs"],
            "cooking": ["Cooking"]
        }

def detect_pain_signals(content: str) -> dict:
    """
    Check if content matches pain detection patterns
    Returns dict with matched patterns and pain score
    """
    content_lower = content.lower()
    matched_patterns = []
    
    for pattern in PAIN_PATTERNS:
        if pattern in content_lower:
            matched_patterns.append(pattern)
    
    pain_score = min(len(matched_patterns) * 2, 10)  # Max score of 10
    
    return {
        'has_pain_signal': len(matched_patterns) > 0,
        'matched_patterns': matched_patterns,
        'pain_score': pain_score
    }

supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

def fetch_reddit_json(subreddit: str, limit: int = 25) -> list:
    """
    Fetch posts from Reddit using the JSON API
    Simply add .json to any Reddit URL!
    """
    url = f'https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}'
    
    headers = {
        'User-Agent': 'ProductGapIntelligence/1.0 (Python/requests)'
    }
    
    print(f'Fetching r/{subreddit}...')
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 429:
            print(f'⚠️  Rate limited on r/{subreddit}, waiting 60s...')
            time.sleep(60)
            response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f'✗ Failed to fetch r/{subreddit}: {response.status_code}')
            return []
        
        data = response.json()
        posts = data['data']['children']
        
        print(f'✓ Fetched {len(posts)} posts from r/{subreddit}')
        return posts
        
    except Exception as e:
        print(f'✗ Error fetching r/{subreddit}: {e}')
        return []

def fetch_post_comments(post_permalink: str) -> list:
    """
    Fetch ALL comments from a post (nested to n-depth)
    """
    url = f'https://www.reddit.com{post_permalink}.json'
    
    headers = {
        'User-Agent': 'ProductGapIntelligence/1.0 (Python/requests)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        
        # Reddit returns [post_data, comments_data]
        comments_data = data[1]['data']['children']
        
        # Flatten nested comments
        all_comments = []
        
        def extract_comments(comment_list):
            for item in comment_list:
                if item['kind'] == 't1':  # Comment type
                    comment_data = item['data']
                    all_comments.append({
                        'body': comment_data.get('body', ''),
                        'score': comment_data.get('score', 0),
                        'author': comment_data.get('author', '[deleted]')
                    })
                    
                    # Recursively get replies
                    if 'replies' in comment_data and comment_data['replies']:
                        if isinstance(comment_data['replies'], dict):
                            extract_comments(comment_data['replies']['data']['children'])
        
        extract_comments(comments_data)
        return all_comments
        
    except Exception as e:
        print(f'  ⚠️  Error fetching comments: {e}')
        return []

def process_reddit_posts(posts: list, subreddit: str, fetch_comments: bool = True) -> list:
    """
    Process Reddit JSON data into our format
    Optionally fetch ALL comments for each post
    """
    processed = []
    
    for post in posts:
        if post['kind'] != 't3':  # Skip non-post items
            continue
        
        data = post['data']
        
        # Basic post data
        post_id = data['id']
        title = data['title']
        selftext = data.get('selftext', '')
        permalink = data['permalink']
        url = f"https://reddit.com{permalink}"
        
        # Combine title and body
        content = title
        if selftext:
            content += f"\n\n{selftext}"
        
        # Get comments if enabled
        comments = []
        if fetch_comments and data.get('num_comments', 0) > 0:
            print(f'  📝 Fetching {data["num_comments"]} comments...')
            comments = fetch_post_comments(permalink)
            time.sleep(2)  # Rate limit: 2s between comment fetches
        
        # Combine content with top comments for better pain detection
        if comments:
            top_comments = sorted(comments, key=lambda x: x['score'], reverse=True)[:10]
            comment_text = '\n'.join([c['body'] for c in top_comments[:5]])
            content += f"\n\nTop comments:\n{comment_text}"
        
        content_hash = hashlib.md5(f"{post_id}{title}".encode()).hexdigest()
        
        # Detect pain signals
        pain_detection = detect_pain_signals(content)
        
        processed.append({
            'platform': 'reddit',
            'post_id': f'reddit_{post_id}',
            'content': content[:5000],  # Limit to 5000 chars
            'author': data.get('author', '[deleted]'),
            'url': url,
            'metrics': {
                'upvotes': data.get('score', 0),
                'comments': data.get('num_comments', 0),
                'upvote_ratio': data.get('upvote_ratio', 0),
                'created_utc': data.get('created_utc', 0),
                'has_pain_signal': pain_detection['has_pain_signal'],
                'pain_patterns': pain_detection['matched_patterns'],
                'pain_score': pain_detection['pain_score']
            },
            'content_hash': content_hash,
            'scraped_at': datetime.now().isoformat(),
            'processed': False
        })
        
        if pain_detection['has_pain_signal']:
            print(f'  🎯 Pain signal detected: {pain_detection["matched_patterns"][:2]}')
    
    return processed

def save_to_supabase(posts: list) -> dict:
    """
    Save posts to Supabase with deduplication
    Returns dict with new_count, duplicate_count, error_count
    """
    if not posts:
        return {'new': 0, 'duplicates': 0, 'errors': 0}
    
    stats = {'new': 0, 'duplicates': 0, 'errors': 0}
    
    try:
        # Get existing content hashes to check for duplicates
        existing_hashes = set()
        try:
            hash_result = supabase.table('raw_posts').select('content_hash').execute()
            existing_hashes = {row['content_hash'] for row in hash_result.data} if hash_result.data else set()
        except Exception:
            pass  # If we can't check, just try to insert all
        
        # Separate new posts from duplicates
        new_posts = []
        for post in posts:
            if post['content_hash'] in existing_hashes:
                stats['duplicates'] += 1
            else:
                new_posts.append(post)
        
        if stats['duplicates'] > 0:
            print(f'⏭️  Skipping {stats["duplicates"]} duplicate posts')
        
        if not new_posts:
            print(f'💾 No new posts to save (all duplicates)')
            return stats
        
        # Upsert new posts (handles any edge cases)
        result = supabase.table('raw_posts').upsert(
            new_posts,
            on_conflict='content_hash'
        ).execute()
        
        stats['new'] = len(result.data) if result.data else len(new_posts)
        print(f'💾 Saved {stats["new"]} new posts to Supabase')
        
        return stats
        
    except Exception as e:
        print(f'✗ Database error: {e}')
        stats['errors'] = len(posts)
        return stats


def get_last_run_timestamp(scraper_name: str) -> float:
    """
    Get the last_run_at timestamp from scraper_metadata
    Returns Unix timestamp or 0 if never run
    """
    try:
        result = supabase.table('scraper_metadata').select('last_run_at').eq('scraper_name', scraper_name).single().execute()
        
        if result.data and result.data.get('last_run_at'):
            # Parse ISO timestamp to Unix timestamp
            last_run = datetime.fromisoformat(result.data['last_run_at'].replace('Z', '+00:00'))
            return last_run.timestamp()
        
        return 0
        
    except Exception as e:
        print(f'⚠️  Could not get last_run_at: {e}')
        return 0


def update_scraper_metadata(scraper_name: str, records_processed: int, status: str = 'completed', error_message: str = None):
    """
    Update scraper_metadata table with run information
    """
    try:
        metadata = {
            'scraper_name': scraper_name,
            'last_run_at': datetime.now(timezone.utc).isoformat(),
            'records_processed': records_processed,
            'status': status,
            'error_message': error_message,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if status == 'completed':
            metadata['last_success_at'] = datetime.now(timezone.utc).isoformat()
        
        supabase.table('scraper_metadata').upsert(
            metadata,
            on_conflict='scraper_name'
        ).execute()
        
        print(f'📝 Updated scraper_metadata for "{scraper_name}"')
        
    except Exception as e:
        print(f'⚠️  Failed to update scraper_metadata: {e}')

def filter_posts_by_timestamp(posts: list, min_timestamp: float) -> list:
    """
    Filter posts to only include those created after min_timestamp
    """
    if min_timestamp == 0:
        return posts  # No filtering if no previous run
    
    filtered = []
    skipped = 0
    
    for post in posts:
        if post['kind'] != 't3':
            continue
        
        created_utc = post['data'].get('created_utc', 0)
        if created_utc > min_timestamp:
            filtered.append(post)
        else:
            skipped += 1
    
    if skipped > 0:
        print(f'  ⏭️  Skipped {skipped} old posts (before last run)')
    
    return filtered


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Reddit Scraper for Product Gap Intelligence')
    
    parser.add_argument(
        '--subreddit', '-s',
        type=str,
        help='Scrape only a specific subreddit (e.g., --subreddit=dogs)'
    )
    
    parser.add_argument(
        '--full', '-f',
        action='store_true',
        help='Full scrape - ignore last_run_at and scrape all posts'
    )
    
    parser.add_argument(
        '--no-comments',
        action='store_true',
        help='Skip fetching comments (faster but less data)'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=25,
        help='Number of posts to fetch per subreddit (default: 25)'
    )
    
    return parser.parse_args()


def main():
    """Main scraper function"""
    
    # Parse command line arguments
    args = parse_args()
    
    # Track start time
    start_time = time.time()
    
    # Get last run timestamp for incremental scraping
    last_run_timestamp = 0
    if not args.full:
        last_run_timestamp = get_last_run_timestamp('reddit_scraper')
        if last_run_timestamp > 0:
            last_run_dt = datetime.fromtimestamp(last_run_timestamp, tz=timezone.utc)
            print(f'⏰ Last run: {last_run_dt.strftime("%Y-%m-%d %H:%M:%S UTC")}')
            print(f'📌 Incremental mode: Only scraping posts newer than last run')
            print(f'   (Use --full to ignore this and scrape all posts)\n')
        else:
            print(f'🆕 First run detected - scraping all posts\n')
    else:
        print(f'🔄 Full scrape mode: Ignoring last_run_at\n')
    
    # Load subreddits from config or use single subreddit
    if args.subreddit:
        subreddits = [args.subreddit]
        print(f'📁 Single subreddit mode: r/{args.subreddit}\n')
    else:
        config = load_subreddits_config()
        subreddits = []
        for category, subs in config.items():
            subreddits.extend(subs)
            print(f'📁 {category}: {", ".join(subs)}')
        print(f'\n📊 Total subreddits to scrape: {len(subreddits)}\n')
    
    # Comment fetching toggle
    FETCH_COMMENTS = not args.no_comments
    
    print(f'🔍 Starting Reddit scraper (comments: {FETCH_COMMENTS}, limit: {args.limit})...\n')
    
    all_posts = []
    posts_skipped_old = 0
    
    for subreddit in subreddits:
        # Fetch posts
        posts = fetch_reddit_json(subreddit, limit=args.limit)
        
        if not posts:
            continue
        
        # Filter posts by timestamp (incremental scraping)
        if last_run_timestamp > 0:
            original_count = len(posts)
            posts = filter_posts_by_timestamp(posts, last_run_timestamp)
            posts_skipped_old += original_count - len(posts)
            
            if not posts:
                print(f'  ✓ No new posts in r/{subreddit}')
                time.sleep(1)  # Shorter delay when skipping
                continue
        
        # Process posts (optionally with comments)
        processed = process_reddit_posts(posts, subreddit, fetch_comments=FETCH_COMMENTS)
        all_posts.extend(processed)
        
        # Rate limit between subreddits
        time.sleep(3)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    print(f'\n📊 Total posts collected: {len(all_posts)}')
    
    # Save to database
    save_stats = save_to_supabase(all_posts)
    
    # Count pain signals
    pain_posts = sum(1 for p in all_posts if p['metrics'].get('has_pain_signal', False))
    
    # Update scraper metadata
    total_processed = save_stats['new'] + save_stats['duplicates']
    if save_stats['errors'] > 0:
        update_scraper_metadata('reddit_scraper', total_processed, 'error', f'{save_stats["errors"]} posts failed')
    else:
        update_scraper_metadata('reddit_scraper', total_processed, 'completed')
    
    # Final summary
    print(f'\n{"="*50}')
    print(f'📊 SCRAPER SUMMARY')
    print(f'{"="*50}')
    print(f'✅ New posts saved:     {save_stats["new"]}')
    print(f'⏭️  Duplicates skipped: {save_stats["duplicates"]}')
    if posts_skipped_old > 0:
        print(f'⏮️  Old posts skipped:  {posts_skipped_old}')
    print(f'❌ Errors:              {save_stats["errors"]}')
    print(f'🎯 Pain signals found:  {pain_posts}/{len(all_posts)}')
    print(f'⏱️  Elapsed time:        {elapsed_time:.1f}s')
    print(f'{"="*50}')
    
    if args.full:
        print(f'💡 Full scrape completed')
    else:
        print(f'💡 Incremental scrape completed (run with --full to scrape all)')

if __name__ == '__main__':
    main()
