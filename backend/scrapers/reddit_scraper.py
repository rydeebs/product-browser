import os
import time
import hashlib
import requests
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

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
                'created_utc': data.get('created_utc', 0)
            },
            'content_hash': content_hash,
            'scraped_at': datetime.now().isoformat(),
            'processed': False
        })
    
    return processed

def save_to_supabase(posts: list) -> int:
    """Save posts to Supabase"""
    if not posts:
        return 0
    
    try:
        result = supabase.table('raw_posts').upsert(
            posts,
            on_conflict='post_id'
        ).execute()
        
        saved_count = len(result.data) if result.data else 0
        print(f'💾 Saved {saved_count} posts to Supabase')
        return saved_count
        
    except Exception as e:
        print(f'✗ Database error: {e}')
        return 0

def main():
    """Main scraper function"""
    
    subreddits = [
        'dogs',
        'BuyItForLife',
        'shutupandtakemymoney',
        'DidntKnowIWantedThat',
        'HomeImprovement',
        'homegym',
        'Cooking'
    ]
    
    # TOGGLE: Set to False to scrape posts only (faster)
    # Set to True to get ALL comments (slower but WAY better data)
    FETCH_COMMENTS = True
    
    print(f'🔍 Starting Reddit scraper (comments: {FETCH_COMMENTS})...\n')
    
    all_posts = []
    
    for subreddit in subreddits:
        # Fetch posts
        posts = fetch_reddit_json(subreddit, limit=25)
        
        if not posts:
            continue
        
        # Process posts (optionally with comments)
        processed = process_reddit_posts(posts, subreddit, fetch_comments=FETCH_COMMENTS)
        all_posts.extend(processed)
        
        # Rate limit between subreddits
        time.sleep(3)
    
    print(f'\n📊 Total posts collected: {len(all_posts)}')
    
    # Save to database
    saved = save_to_supabase(all_posts)
    
    print(f'\n✅ Complete! {saved} posts saved to database')
    print(f'💡 Posts now include comment data for richer pain point detection')

if __name__ == '__main__':
    main()
