"""
Twitter/X Scraper for Product Browser

Scrapes tweets for product opportunities and pain points.
Uses multiple methods:
1. Nitter instances (no API required)
2. Direct X access (if user authenticated)
3. Manual tweet input

Stores both raw tweets (evidence) and extracted insights.
"""

import os
import sys
import json
import time
import hashlib
import argparse
import requests
from datetime import datetime, timezone
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

# ============================================================
# NITTER INSTANCES (Public Twitter Frontends)
# ============================================================

# List of Nitter instances to try (they go up/down frequently)
# Check https://status.d420.de/nitter or https://github.com/zedeus/nitter/wiki/Instances
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org", 
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
    "https://nitter.unixfox.eu",
    "https://nitter.fdn.fr",
    "https://nitter.it",
    "https://nitter.net",
    "https://nitter.cz",
    "https://nitter.hu",
    "https://nitter.nl",
    "https://nitter.ca",
    "https://nitter.eu",
    "https://bird.trom.tf",
    "https://nitter.esmailelbob.xyz",
    "https://nitter.weiler.rocks",
    "https://nitter.sethforprivacy.com",
    "https://nitter.cutelab.space",
    "https://nitter.fly.dev",
    "https://nitter.mint.lgbt",
    "https://nitter.lunar.icu",
]

# ============================================================
# PAIN SIGNAL PATTERNS (Twitter-specific)
# ============================================================

TWITTER_PAIN_PATTERNS = [
    # Direct product requests
    "someone should build",
    "someone should make",
    "someone needs to build",
    "someone needs to make",
    "why isn't there",
    "why doesn't exist",
    "why is there no",
    "why hasn't anyone built",
    "why hasn't anyone made",
    
    # Money signals (high value!)
    "i would pay for",
    "i'd pay for",
    "take my money",
    "shut up and take my money",
    "would definitely buy",
    "instant purchase",
    "day one purchase",
    "would pay good money",
    "$10/mo",
    "$20/mo",
    "$50/mo",
    "$100/mo",
    
    # Frustration signals
    "so frustrated with",
    "frustrated that",
    "hate that there's no",
    "can't believe there isn't",
    "why is it so hard to",
    "tired of",
    "sick of",
    "annoyed that",
    "drives me crazy",
    
    # Wish/want signals
    "i wish there was",
    "i wish someone made",
    "i wish someone built",
    "would love a",
    "need a better",
    "looking for a",
    "anyone know of a",
    "does anyone know",
    "is there an app",
    "is there a tool",
    "is there a service",
    
    # Idea signals
    "startup idea:",
    "product idea:",
    "app idea:",
    "saas idea:",
    "billion dollar idea",
    "million dollar idea",
    "free startup idea",
    "someone steal this idea",
    
    # Problem statements
    "biggest pain point",
    "major problem with",
    "the problem is",
    "struggling to find",
    "can't find a good",
    "there's no good",
    
    # Validation signals
    "is there a product",
    "does anyone make",
    "has anyone built",
    "looking for recommendations",
]

# High-value accounts to monitor (founders, builders, VCs)
HIGH_VALUE_ACCOUNTS = [
    "levelsio",       # Pieter Levels - indie hacker
    "nateliason",     # Nat Eliason - creator/founder
    "gregisenberg",   # Greg Isenberg - community/startup ideas
    "Julian",         # Julian Shapiro
    "dhabordeaux",    # Dan Habordeaux
    "tdinh_me",       # Tony Dinh - indie hacker
    "marc_louvion",   # Marc Louvion - indie hacker  
    "dannypostmaa",   # Danny Postma - indie hacker
    "arabordeaux",    # Product ideas
    "swyx",           # Shawn Wang - developer
    "pabordeaux",     # Startup trends
    "patrick_oshag",  # Patrick O'Shaughnessy
    "naval",          # Naval Ravikant
    "paulg",          # Paul Graham
]

# Hashtags to track
HASHTAGS_TO_TRACK = [
    "buildinpublic",
    "indiehackers",
    "startupideas",
    "productidea",
    "saas",
    "nocode",
    "shutupandtakemymoney",
    "startup",
    "entrepreneur",
    "solopreneur",
]


# ============================================================
# NITTER SCRAPING
# ============================================================

def get_working_nitter_instance() -> Optional[str]:
    """Find a working Nitter instance that actually returns content"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    print("🔍 Searching for working Nitter instance...")
    
    for instance in NITTER_INSTANCES:
        try:
            # Test with a known account
            test_url = f"{instance}/elonmusk"
            response = requests.get(test_url, headers=headers, timeout=8, allow_redirects=True)
            
            # Check if we got actual content (not just a 200 with empty body)
            if response.status_code == 200 and len(response.text) > 5000:
                # Verify it has tweet content
                if 'timeline-item' in response.text or 'tweet-content' in response.text or 'tweet-body' in response.text:
                    print(f"✅ Using Nitter instance: {instance}")
                    return instance
                else:
                    print(f"  ⚠️ {instance}: No tweet content found")
            else:
                print(f"  ⚠️ {instance}: Status {response.status_code}, Content: {len(response.text)} bytes")
        except requests.exceptions.Timeout:
            print(f"  ⚠️ {instance}: Timeout")
        except Exception as e:
            print(f"  ⚠️ {instance}: {type(e).__name__}")
        
        time.sleep(0.5)  # Small delay between checks
    
    print("\n❌ No working Nitter instance found")
    print("   Nitter instances are frequently down due to Twitter/X API changes.")
    return None


def scrape_nitter_user(username: str, nitter_base: str, limit: int = 20) -> List[Dict]:
    """
    Scrape tweets from a user's profile via Nitter
    
    Args:
        username: Twitter username (without @)
        nitter_base: Base URL of Nitter instance
        limit: Max tweets to fetch
    
    Returns:
        List of tweet dictionaries
    """
    url = f"{nitter_base}/{username}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    print(f"Fetching @{username}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"  ✗ Failed to fetch @{username}: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tweets = []
        
        # Find tweet containers (Nitter structure)
        tweet_containers = soup.find_all('div', class_='timeline-item')[:limit]
        
        for container in tweet_containers:
            try:
                # Extract tweet content
                content_elem = container.find('div', class_='tweet-content')
                if not content_elem:
                    continue
                
                content = content_elem.get_text(strip=True)
                
                # Extract tweet link/ID
                link_elem = container.find('a', class_='tweet-link')
                tweet_url = ""
                tweet_id = ""
                if link_elem:
                    href = link_elem.get('href', '')
                    tweet_id = href.split('/')[-1].replace('#m', '')
                    tweet_url = f"https://x.com{href.replace('#m', '')}"
                
                # Extract stats
                stats = container.find('div', class_='tweet-stats')
                likes = 0
                retweets = 0
                replies = 0
                
                if stats:
                    # Parse stats (format varies by Nitter instance)
                    stat_items = stats.find_all('span', class_='tweet-stat')
                    for stat in stat_items:
                        text = stat.get_text(strip=True).lower()
                        icon = stat.find('span', class_='icon')
                        if icon:
                            icon_class = ' '.join(icon.get('class', []))
                            if 'heart' in icon_class or 'like' in icon_class:
                                likes = parse_stat_number(text)
                            elif 'retweet' in icon_class:
                                retweets = parse_stat_number(text)
                            elif 'comment' in icon_class or 'reply' in icon_class:
                                replies = parse_stat_number(text)
                
                # Extract timestamp
                time_elem = container.find('span', class_='tweet-date')
                timestamp = None
                if time_elem:
                    time_link = time_elem.find('a')
                    if time_link:
                        timestamp = time_link.get('title', '')
                
                # Detect pain signals
                pain_info = detect_pain_signals(content)
                
                tweets.append({
                    'platform_id': tweet_id,
                    'content': content,
                    'author': f"@{username}",
                    'url': tweet_url,
                    'timestamp': timestamp,
                    'metrics': {
                        'likes': likes,
                        'retweets': retweets,
                        'replies': replies,
                        'has_pain_signal': pain_info['has_pain_signal'],
                        'pain_patterns': pain_info['matched_patterns'],
                        'pain_score': pain_info['pain_score']
                    }
                })
                
            except Exception as e:
                print(f"  ⚠️ Error parsing tweet: {e}")
                continue
        
        pain_count = sum(1 for t in tweets if t['metrics'].get('has_pain_signal'))
        print(f"  ✓ Got {len(tweets)} tweets from @{username} ({pain_count} with pain signals)")
        
        return tweets
        
    except Exception as e:
        print(f"  ✗ Error fetching @{username}: {e}")
        return []


def scrape_nitter_search(query: str, nitter_base: str, limit: int = 50) -> List[Dict]:
    """
    Search tweets via Nitter
    
    Args:
        query: Search query (keyword, hashtag, etc.)
        nitter_base: Base URL of Nitter instance
        limit: Max tweets to fetch
    
    Returns:
        List of tweet dictionaries
    """
    # URL encode the query
    encoded_query = requests.utils.quote(query)
    url = f"{nitter_base}/search?f=tweets&q={encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    print(f"Searching: {query}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"  ✗ Search failed: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tweets = []
        
        tweet_containers = soup.find_all('div', class_='timeline-item')[:limit]
        
        for container in tweet_containers:
            try:
                content_elem = container.find('div', class_='tweet-content')
                if not content_elem:
                    continue
                
                content = content_elem.get_text(strip=True)
                
                # Extract author
                author_elem = container.find('a', class_='username')
                author = author_elem.get_text(strip=True) if author_elem else "unknown"
                
                # Extract tweet link/ID
                link_elem = container.find('a', class_='tweet-link')
                tweet_url = ""
                tweet_id = ""
                if link_elem:
                    href = link_elem.get('href', '')
                    tweet_id = href.split('/')[-1].replace('#m', '')
                    tweet_url = f"https://x.com{href.replace('#m', '')}"
                
                # Detect pain signals
                pain_info = detect_pain_signals(content)
                
                tweets.append({
                    'platform_id': tweet_id,
                    'content': content,
                    'author': author,
                    'url': tweet_url,
                    'metrics': {
                        'likes': 0,
                        'retweets': 0,
                        'replies': 0,
                        'has_pain_signal': pain_info['has_pain_signal'],
                        'pain_patterns': pain_info['matched_patterns'],
                        'pain_score': pain_info['pain_score']
                    }
                })
                
            except Exception as e:
                continue
        
        pain_count = sum(1 for t in tweets if t['metrics'].get('has_pain_signal'))
        print(f"  ✓ Found {len(tweets)} tweets ({pain_count} with pain signals)")
        
        return tweets
        
    except Exception as e:
        print(f"  ✗ Search error: {e}")
        return []


def parse_stat_number(text: str) -> int:
    """Parse stat numbers like '1.2K' or '500'"""
    text = text.strip().upper()
    
    # Remove non-numeric prefix
    for char in text:
        if char.isdigit() or char in '.KMB':
            break
        text = text[1:]
    
    if not text:
        return 0
    
    try:
        if 'K' in text:
            return int(float(text.replace('K', '')) * 1000)
        elif 'M' in text:
            return int(float(text.replace('M', '')) * 1000000)
        elif 'B' in text:
            return int(float(text.replace('B', '')) * 1000000000)
        else:
            return int(float(text))
    except:
        return 0


# ============================================================
# PAIN SIGNAL DETECTION
# ============================================================

def detect_pain_signals(content: str) -> dict:
    """
    Check if content matches pain detection patterns
    Returns dict with matched patterns and pain score
    """
    content_lower = content.lower()
    matched_patterns = []
    
    for pattern in TWITTER_PAIN_PATTERNS:
        if pattern in content_lower:
            matched_patterns.append(pattern)
    
    # Higher weight for money signals
    money_signals = ['pay', 'money', '$', 'purchase', 'buy']
    money_bonus = sum(2 for m in money_signals if m in content_lower)
    
    pain_score = min(len(matched_patterns) * 2 + money_bonus, 10)
    
    return {
        'has_pain_signal': len(matched_patterns) > 0,
        'matched_patterns': matched_patterns,
        'pain_score': pain_score
    }


# ============================================================
# DATABASE OPERATIONS
# ============================================================

def generate_content_hash(platform_id: str, content: str) -> str:
    """Generate hash for deduplication"""
    hash_input = f"twitter:{platform_id}:{content[:200]}"
    return hashlib.md5(hash_input.encode()).hexdigest()


def save_tweets_to_supabase(tweets: List[Dict]) -> dict:
    """
    Save tweets to Supabase raw_posts table with deduplication
    
    Returns:
        Stats dict with new, duplicates, errors counts
    """
    stats = {'new': 0, 'duplicates': 0, 'errors': 0}
    
    if not tweets:
        return stats
    
    for tweet in tweets:
        try:
            # Use platform_id from tweet data
            tweet_id = tweet.get('platform_id', '')
            content = tweet.get('content', '')
            
            content_hash = generate_content_hash(tweet_id, content)
            
            # Check for duplicates
            existing = supabase.table('raw_posts')\
                .select('id')\
                .eq('content_hash', content_hash)\
                .execute()
            
            if existing.data:
                stats['duplicates'] += 1
                continue
            
            # Prepare record (using 'post_id' as per schema)
            record = {
                'platform': 'twitter',
                'post_id': tweet_id,  # Schema uses 'post_id' not 'platform_id'
                'content': content[:5000],
                'url': tweet.get('url', ''),
                'author': tweet.get('author', ''),
                'content_hash': content_hash,
                'metrics': tweet.get('metrics', {}),
                'scraped_at': datetime.now(timezone.utc).isoformat(),
            }
            
            # Insert
            supabase.table('raw_posts').insert(record).execute()
            stats['new'] += 1
            
            if tweet.get('metrics', {}).get('has_pain_signal'):
                print(f"  🎯 Pain signal: {tweet['content'][:60]}...")
            
        except Exception as e:
            stats['errors'] += 1
            print(f"  ❌ Error saving tweet: {e}")
    
    return stats


# ============================================================
# MANUAL TWEET INPUT
# ============================================================

def process_manual_tweet(tweet_url: str, content: str, author: str = None) -> dict:
    """
    Process a manually input tweet
    
    Args:
        tweet_url: Full URL to the tweet
        content: Tweet text content
        author: Optional author username
    
    Returns:
        Processed tweet dict
    """
    # Extract tweet ID from URL
    tweet_id = ""
    if '/status/' in tweet_url:
        tweet_id = tweet_url.split('/status/')[-1].split('?')[0].split('/')[0]
    
    # Extract author from URL if not provided
    if not author and 'x.com/' in tweet_url:
        author = '@' + tweet_url.split('x.com/')[-1].split('/')[0]
    elif not author and 'twitter.com/' in tweet_url:
        author = '@' + tweet_url.split('twitter.com/')[-1].split('/')[0]
    
    pain_info = detect_pain_signals(content)
    
    return {
        'platform_id': tweet_id,
        'content': content,
        'author': author or 'unknown',
        'url': tweet_url,
        'metrics': {
            'likes': 0,
            'retweets': 0,
            'replies': 0,
            'has_pain_signal': pain_info['has_pain_signal'],
            'pain_patterns': pain_info['matched_patterns'],
            'pain_score': pain_info['pain_score']
        }
    }


def add_tweet_manually():
    """Interactive mode to add tweets manually"""
    print("\n📝 Manual Tweet Input Mode")
    print("Enter tweet details (or 'q' to quit)\n")
    
    tweets_added = 0
    
    while True:
        url = input("Tweet URL (or 'q' to quit): ").strip()
        if url.lower() == 'q':
            break
        
        content = input("Tweet content: ").strip()
        if not content:
            print("⚠️  Content required")
            continue
        
        author = input("Author (optional, press Enter to skip): ").strip()
        
        tweet = process_manual_tweet(url, content, author if author else None)
        
        # Show pain analysis
        if tweet['metrics']['has_pain_signal']:
            print(f"\n🎯 Pain signals detected!")
            print(f"   Score: {tweet['metrics']['pain_score']}/10")
            print(f"   Patterns: {', '.join(tweet['metrics']['pain_patterns'][:3])}")
        else:
            print(f"\n📊 No strong pain signals detected")
        
        save = input("\nSave this tweet? (y/n): ").strip().lower()
        if save == 'y':
            stats = save_tweets_to_supabase([tweet])
            if stats['new'] > 0:
                print("✅ Tweet saved!")
                tweets_added += 1
            else:
                print("⚠️  Tweet already exists or error occurred")
        
        print()
    
    print(f"\n✅ Added {tweets_added} tweets")


def import_tweets_from_json(filepath: str) -> dict:
    """
    Import tweets from a JSON file
    
    Expected format:
    [
        {
            "url": "https://x.com/user/status/123",
            "content": "Tweet text here",
            "author": "@username"  // optional
        },
        ...
    ]
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        tweets = []
        for item in data:
            tweet = process_manual_tweet(
                tweet_url=item.get('url', ''),
                content=item.get('content', item.get('text', '')),
                author=item.get('author', item.get('username'))
            )
            tweets.append(tweet)
        
        print(f"📂 Loaded {len(tweets)} tweets from {filepath}")
        
        # Save to database
        stats = save_tweets_to_supabase(tweets)
        
        pain_count = sum(1 for t in tweets if t.get('metrics', {}).get('has_pain_signal'))
        print(f"🎯 Pain signals found: {pain_count}/{len(tweets)}")
        
        return stats
        
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return {'new': 0, 'duplicates': 0, 'errors': 1}
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return {'new': 0, 'duplicates': 0, 'errors': 1}


def quick_add_tweet(url: str, content: str, author: str = None) -> dict:
    """
    Quickly add a single tweet without interactive prompts
    Useful for scripting or API calls
    
    Args:
        url: Tweet URL
        content: Tweet text
        author: Optional author username
    
    Returns:
        Stats dict
    """
    tweet = process_manual_tweet(url, content, author)
    
    pain_info = tweet['metrics']
    if pain_info['has_pain_signal']:
        print(f"🎯 Pain signal detected! Score: {pain_info['pain_score']}/10")
        print(f"   Patterns: {', '.join(pain_info['pain_patterns'][:3])}")
    
    stats = save_tweets_to_supabase([tweet])
    
    if stats['new'] > 0:
        print("✅ Tweet saved!")
    elif stats['duplicates'] > 0:
        print("⚠️  Tweet already exists")
    
    return stats


# ============================================================
# MAIN SCRAPER
# ============================================================

def scrape_twitter(
    accounts: List[str] = None,
    hashtags: List[str] = None,
    search_queries: List[str] = None,
    limit_per_source: int = 20
) -> dict:
    """
    Main Twitter scraping function
    
    Args:
        accounts: List of usernames to scrape
        hashtags: List of hashtags to search
        search_queries: Custom search queries
        limit_per_source: Max tweets per account/hashtag
    
    Returns:
        Stats dictionary
    """
    # Find working Nitter instance
    nitter = get_working_nitter_instance()
    
    if not nitter:
        print("\n❌ No Nitter instance available. Try:")
        print("   1. Wait a few minutes and try again")
        print("   2. Use manual tweet input: python twitter_scraper.py --manual")
        print("   3. Check https://status.d420.de/nitter for instance status")
        return {'new': 0, 'duplicates': 0, 'errors': 0, 'nitter_down': True}
    
    all_tweets = []
    
    # Scrape accounts
    if accounts:
        print(f"\n👤 Scraping {len(accounts)} accounts...")
        for username in accounts:
            tweets = scrape_nitter_user(username, nitter, limit=limit_per_source)
            all_tweets.extend(tweets)
            time.sleep(2)  # Rate limiting
    
    # Search hashtags
    if hashtags:
        print(f"\n#️⃣ Searching {len(hashtags)} hashtags...")
        for hashtag in hashtags:
            query = f"#{hashtag}" if not hashtag.startswith('#') else hashtag
            tweets = scrape_nitter_search(query, nitter, limit=limit_per_source)
            all_tweets.extend(tweets)
            time.sleep(2)
    
    # Custom searches
    if search_queries:
        print(f"\n🔍 Running {len(search_queries)} custom searches...")
        for query in search_queries:
            tweets = scrape_nitter_search(query, nitter, limit=limit_per_source)
            all_tweets.extend(tweets)
            time.sleep(2)
    
    # Save to database
    print(f"\n💾 Saving {len(all_tweets)} tweets to database...")
    stats = save_tweets_to_supabase(all_tweets)
    
    # Summary
    pain_count = sum(1 for t in all_tweets if t.get('metrics', {}).get('has_pain_signal'))
    
    print(f"\n{'='*50}")
    print(f"📊 TWITTER SCRAPER SUMMARY")
    print(f"{'='*50}")
    print(f"✅ New tweets saved:    {stats['new']}")
    print(f"⏭️  Duplicates skipped: {stats['duplicates']}")
    print(f"❌ Errors:              {stats['errors']}")
    print(f"🎯 Pain signals found:  {pain_count}/{len(all_tweets)}")
    print(f"{'='*50}")
    
    return stats


# ============================================================
# CLI
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Twitter/X Scraper for Product Browser')
    
    parser.add_argument(
        '--accounts', '-a',
        type=str,
        help='Comma-separated list of accounts to scrape (e.g., levelsio,nateliason)'
    )
    
    parser.add_argument(
        '--hashtags', '-t',
        type=str,
        help='Comma-separated hashtags to search (e.g., buildinpublic,startupideas)'
    )
    
    parser.add_argument(
        '--search', '-s',
        type=str,
        help='Custom search query'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=20,
        help='Max tweets per source (default: 20)'
    )
    
    parser.add_argument(
        '--manual', '-m',
        action='store_true',
        help='Manual tweet input mode (interactive)'
    )
    
    parser.add_argument(
        '--import-json', '-i',
        type=str,
        metavar='FILE',
        help='Import tweets from a JSON file'
    )
    
    parser.add_argument(
        '--add',
        nargs=2,
        metavar=('URL', 'CONTENT'),
        help='Quickly add a single tweet: --add "url" "content"'
    )
    
    parser.add_argument(
        '--default',
        action='store_true',
        help='Use default high-value accounts and hashtags'
    )
    
    parser.add_argument(
        '--pain-only',
        action='store_true',
        help='Only save tweets with pain signals'
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("🐦 Twitter/X Scraper for Product Browser")
    print("=" * 50)
    
    # Handle manual input mode
    if args.manual:
        add_tweet_manually()
        return
    
    # Handle JSON import
    if args.import_json:
        stats = import_tweets_from_json(args.import_json)
        print(f"\n✅ Import complete: {stats['new']} new, {stats['duplicates']} duplicates")
        return
    
    # Handle quick add
    if args.add:
        url, content = args.add
        quick_add_tweet(url, content)
        return
    
    # Parse arguments for Nitter scraping
    accounts = None
    hashtags = None
    search_queries = None
    
    if args.default:
        accounts = HIGH_VALUE_ACCOUNTS[:10]  # Top 10 accounts
        hashtags = HASHTAGS_TO_TRACK[:5]      # Top 5 hashtags
        search_queries = [
            "someone should build",
            "i would pay for",
            "why isn't there",
            "startup idea",
        ]
    
    if args.accounts:
        accounts = [a.strip().replace('@', '') for a in args.accounts.split(',')]
    
    if args.hashtags:
        hashtags = [h.strip().replace('#', '') for h in args.hashtags.split(',')]
    
    if args.search:
        search_queries = [args.search]
    
    if not accounts and not hashtags and not search_queries:
        print("\n📋 USAGE OPTIONS:")
        print()
        print("  Nitter Scraping (when instances are available):")
        print("   --default              Use default accounts and hashtags")
        print("   --accounts=user1,user2 Scrape specific accounts")
        print("   --hashtags=tag1,tag2   Search hashtags")
        print("   --search='query'       Custom search query")
        print()
        print("  Manual Input (always works):")
        print("   --manual               Interactive tweet input")
        print("   --add 'url' 'content'  Quick add single tweet")
        print("   --import-json file.json Import from JSON file")
        print()
        print("  Example JSON format for --import-json:")
        print('   [{"url": "https://x.com/...", "content": "Tweet text", "author": "@user"}]')
        print()
        return
    
    # Run Nitter scraper
    scrape_twitter(
        accounts=accounts,
        hashtags=hashtags,
        search_queries=search_queries,
        limit_per_source=args.limit
    )


if __name__ == '__main__':
    main()

