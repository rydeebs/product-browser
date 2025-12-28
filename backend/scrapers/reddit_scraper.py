import os
import time
import hashlib
from datetime import datetime
from supabase import create_client, Client
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')  # Use service key for server-side
)

def scrape_subreddit(subreddit: str, page) -> list:
    """Scrape posts from a subreddit using Playwright"""
    url = f'https://old.reddit.com/r/{subreddit}/hot'
    
    print(f'Scraping r/{subreddit}...')
    
    try:
        page.goto(url, timeout=30000)
        page.wait_for_selector('.thing', timeout=10000)
        
        posts = []
        post_elements = page.query_selector_all('.thing')[:25]
        
        for element in post_elements:
            try:
                title_el = element.query_selector('.title a.title')
                if not title_el:
                    continue
                
                title = title_el.inner_text().strip()
                url = title_el.get_attribute('href') or ''
                post_id = element.get_attribute('data-fullname') or f"post_{hash(title)}"
                
                score_el = element.query_selector('.score.unvoted')
                score = score_el.inner_text() if score_el else '0'
                
                comments_el = element.query_selector('.comments')
                comments_text = comments_el.inner_text() if comments_el else '0'
                num_comments = 0
                if 'comment' in comments_text:
                    import re
                    match = re.search(r'(\d+)', comments_text)
                    if match:
                        num_comments = int(match.group(1))
                
                # Create content hash for deduplication
                content_hash = hashlib.md5(f"{post_id}{title}".encode()).hexdigest()
                
                posts.append({
                    'platform': 'reddit',
                    'post_id': f'reddit_{post_id}',
                    'content': title,
                    'author': 'unknown',
                    'url': url if url.startswith('http') else f'https://reddit.com{url}',
                    'metrics': {
                        'upvotes': int(score) if score.isdigit() else 0,
                        'comments': num_comments
                    },
                    'content_hash': content_hash,
                    'scraped_at': datetime.now().isoformat(),
                    'processed': False
                })
            except Exception as e:
                print(f'Error parsing post: {e}')
                continue
        
        print(f'✓ Scraped {len(posts)} posts from r/{subreddit}')
        return posts
        
    except Exception as e:
        print(f'✗ Failed to scrape r/{subreddit}: {e}')
        return []

def save_to_supabase(posts: list) -> int:
    """Save posts to Supabase, handling duplicates"""
    if not posts:
        return 0
    
    try:
        # Upsert posts (insert or update on conflict)
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
    
    all_posts = []
    
    with sync_playwright() as p:
        # Launch browser (headless)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        for subreddit in subreddits:
            posts = scrape_subreddit(subreddit, page)
            all_posts.extend(posts)
            
            # Wait 2 seconds between subreddits
            time.sleep(2)
        
        browser.close()
    
    print(f'\n📊 Total posts scraped: {len(all_posts)}')
    
    # Save to Supabase
    saved = save_to_supabase(all_posts)
    print(f'✅ Complete! {saved} posts saved to database')

if __name__ == '__main__':
    main()
