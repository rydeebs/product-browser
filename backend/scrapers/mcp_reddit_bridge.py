"""
MCP Reddit Bridge - Integrates mcp-reddit data with Product Browser

This module provides utilities to:
1. Process data scraped via mcp-reddit MCP server
2. Import MCP-scraped data into Supabase
3. Work alongside the PRAW-based scraper

Usage:
- MCP scraping: Use Claude with mcp-reddit for interactive scraping
- Automated scraping: Use reddit_scraper.py with PRAW for GitHub Actions
- Data import: Use this bridge to sync MCP data to Supabase

MCP Reddit stores data in ~/.mcp-reddit/data/ by default
(or MCP_REDDIT_DATA_DIR if set)
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

# Pain detection patterns (same as reddit_scraper.py)
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


def get_mcp_data_dir() -> Path:
    """Get the MCP Reddit data directory"""
    custom_dir = os.getenv('MCP_REDDIT_DATA_DIR')
    if custom_dir:
        return Path(custom_dir)
    return Path.home() / '.mcp-reddit' / 'data'


def detect_pain_signals(content: str) -> dict:
    """Check if content matches pain detection patterns"""
    content_lower = content.lower()
    matched_patterns = []
    
    for pattern in PAIN_PATTERNS:
        if pattern in content_lower:
            matched_patterns.append(pattern)
    
    pain_score = min(len(matched_patterns) * 2, 10)
    
    return {
        'has_pain_signal': len(matched_patterns) > 0,
        'matched_patterns': matched_patterns,
        'pain_score': pain_score
    }


def generate_content_hash(post_id: str, content: str) -> str:
    """Generate a hash for deduplication"""
    hash_input = f"{post_id}:{content[:500]}"
    return hashlib.md5(hash_input.encode()).hexdigest()


def load_mcp_posts(subreddit: Optional[str] = None) -> list:
    """
    Load posts from MCP Reddit's local storage.
    
    Args:
        subreddit: Optional filter by subreddit name
    
    Returns:
        List of post dictionaries
    """
    data_dir = get_mcp_data_dir()
    
    if not data_dir.exists():
        print(f"⚠️  MCP data directory not found: {data_dir}")
        print("   Run 'claude mcp add reddit -- uvx mcp-reddit' and scrape some subreddits first")
        return []
    
    posts = []
    
    # MCP Reddit stores data in JSON files
    for json_file in data_dir.glob('**/*.json'):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Handle different data structures
            if isinstance(data, list):
                for item in data:
                    if subreddit and item.get('subreddit', '').lower() != subreddit.lower():
                        continue
                    posts.append(item)
            elif isinstance(data, dict):
                if 'posts' in data:
                    for post in data['posts']:
                        if subreddit and post.get('subreddit', '').lower() != subreddit.lower():
                            continue
                        posts.append(post)
                else:
                    if subreddit and data.get('subreddit', '').lower() != subreddit.lower():
                        continue
                    posts.append(data)
                    
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse {json_file}")
        except Exception as e:
            print(f"⚠️  Error reading {json_file}: {e}")
    
    print(f"📂 Loaded {len(posts)} posts from MCP Reddit data")
    return posts


def transform_mcp_post(mcp_post: dict) -> dict:
    """
    Transform an MCP Reddit post to match our Supabase schema.
    
    Args:
        mcp_post: Post dictionary from MCP Reddit
    
    Returns:
        Transformed post for Supabase
    """
    # Extract fields (MCP Reddit may use different field names)
    post_id = mcp_post.get('id') or mcp_post.get('post_id') or ''
    title = mcp_post.get('title', '')
    content = mcp_post.get('selftext') or mcp_post.get('content') or mcp_post.get('body') or ''
    subreddit = mcp_post.get('subreddit', '').replace('r/', '')
    author = mcp_post.get('author', '[unknown]')
    url = mcp_post.get('url') or mcp_post.get('permalink') or ''
    
    # Handle URL formatting
    if url and not url.startswith('http'):
        url = f'https://reddit.com{url}'
    
    # Extract metrics
    upvotes = mcp_post.get('score') or mcp_post.get('upvotes') or mcp_post.get('ups') or 0
    comments = mcp_post.get('num_comments') or mcp_post.get('comments_count') or 0
    upvote_ratio = mcp_post.get('upvote_ratio', 0.5)
    
    # Handle timestamp
    created_utc = mcp_post.get('created_utc') or mcp_post.get('created')
    if isinstance(created_utc, (int, float)):
        created_at = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()
    elif isinstance(created_utc, str):
        created_at = created_utc
    else:
        created_at = datetime.now(timezone.utc).isoformat()
    
    # Detect pain signals
    full_content = f"{title} {content}"
    pain_info = detect_pain_signals(full_content)
    
    # Generate content hash for deduplication
    content_hash = generate_content_hash(post_id, full_content)
    
    return {
        'platform': 'reddit',
        'platform_id': post_id,
        'content': full_content[:5000],  # Limit content length
        'url': url,
        'author': author,
        'subreddit': subreddit,
        'created_at': created_at,
        'scraped_at': datetime.now(timezone.utc).isoformat(),
        'content_hash': content_hash,
        'metrics': {
            'upvotes': upvotes,
            'comments': comments,
            'upvote_ratio': upvote_ratio,
            'has_pain_signal': pain_info['has_pain_signal'],
            'pain_patterns': pain_info['matched_patterns'],
            'pain_score': pain_info['pain_score']
        },
        'source': 'mcp-reddit'  # Track data source
    }


def import_mcp_posts_to_supabase(subreddit: Optional[str] = None, limit: int = 100) -> dict:
    """
    Import MCP Reddit posts to Supabase with deduplication.
    
    Args:
        subreddit: Optional filter by subreddit
        limit: Maximum posts to import
    
    Returns:
        Stats dictionary with counts
    """
    stats = {'new': 0, 'duplicates': 0, 'errors': 0}
    
    # Load posts from MCP data
    mcp_posts = load_mcp_posts(subreddit)
    
    if not mcp_posts:
        print("❌ No posts to import")
        return stats
    
    # Limit posts
    mcp_posts = mcp_posts[:limit]
    
    print(f"📤 Importing {len(mcp_posts)} posts to Supabase...")
    
    for mcp_post in mcp_posts:
        try:
            # Transform to our schema
            post = transform_mcp_post(mcp_post)
            
            # Check for duplicates by content_hash
            existing = supabase.table('raw_posts')\
                .select('id')\
                .eq('content_hash', post['content_hash'])\
                .execute()
            
            if existing.data:
                stats['duplicates'] += 1
                continue
            
            # Insert new post
            supabase.table('raw_posts').insert(post).execute()
            stats['new'] += 1
            
            if post['metrics'].get('has_pain_signal'):
                print(f"  🎯 Pain signal: {post['subreddit']} - {post['content'][:50]}...")
            
        except Exception as e:
            stats['errors'] += 1
            print(f"  ❌ Error: {e}")
    
    print(f"\n✅ Import complete: {stats['new']} new, {stats['duplicates']} duplicates, {stats['errors']} errors")
    return stats


def list_mcp_subreddits() -> list:
    """List all subreddits available in MCP Reddit data"""
    posts = load_mcp_posts()
    subreddits = set()
    
    for post in posts:
        sub = post.get('subreddit', '').replace('r/', '')
        if sub:
            subreddits.add(sub)
    
    return sorted(subreddits)


def get_pain_posts_from_mcp(min_score: int = 2) -> list:
    """
    Get posts with pain signals from MCP data.
    
    Args:
        min_score: Minimum pain score to include
    
    Returns:
        List of posts with pain signals
    """
    posts = load_mcp_posts()
    pain_posts = []
    
    for mcp_post in posts:
        post = transform_mcp_post(mcp_post)
        if post['metrics'].get('pain_score', 0) >= min_score:
            pain_posts.append(post)
    
    # Sort by pain score (descending)
    pain_posts.sort(key=lambda p: p['metrics'].get('pain_score', 0), reverse=True)
    
    return pain_posts


# ============================================================
# CLI INTERFACE
# ============================================================

def main():
    """CLI interface for MCP Reddit Bridge"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP Reddit Bridge - Import MCP data to Supabase')
    
    parser.add_argument(
        '--import', '-i',
        dest='do_import',
        action='store_true',
        help='Import MCP Reddit posts to Supabase'
    )
    
    parser.add_argument(
        '--subreddit', '-s',
        type=str,
        help='Filter by subreddit'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=100,
        help='Maximum posts to import (default: 100)'
    )
    
    parser.add_argument(
        '--list-subreddits',
        action='store_true',
        help='List available subreddits in MCP data'
    )
    
    parser.add_argument(
        '--pain-posts',
        action='store_true',
        help='Show posts with pain signals'
    )
    
    parser.add_argument(
        '--min-pain-score',
        type=int,
        default=2,
        help='Minimum pain score for --pain-posts (default: 2)'
    )
    
    args = parser.parse_args()
    
    if args.list_subreddits:
        print("📂 Subreddits in MCP Reddit data:")
        for sub in list_mcp_subreddits():
            print(f"  • r/{sub}")
        return
    
    if args.pain_posts:
        print(f"🎯 Posts with pain signals (score >= {args.min_pain_score}):\n")
        pain_posts = get_pain_posts_from_mcp(args.min_pain_score)
        
        for post in pain_posts[:20]:  # Show top 20
            score = post['metrics'].get('pain_score', 0)
            patterns = post['metrics'].get('pain_patterns', [])
            print(f"[{score}/10] r/{post['subreddit']}")
            print(f"  {post['content'][:100]}...")
            print(f"  Patterns: {', '.join(patterns[:3])}")
            print()
        
        print(f"Total: {len(pain_posts)} posts with pain signals")
        return
    
    if args.do_import:
        import_mcp_posts_to_supabase(
            subreddit=args.subreddit,
            limit=args.limit
        )
        return
    
    # Default: show help
    parser.print_help()


if __name__ == '__main__':
    main()

