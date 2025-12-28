from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')  # Use service key for server-side
)

def save_posts(posts):
    """Save scraped posts to Supabase"""
    data = supabase.table('raw_posts').insert(posts).execute()
    return data

def get_unprocessed_posts(limit=50):
    """Get posts that haven't been analyzed"""
    data = supabase.table('raw_posts')\
        .select('*')\
        .eq('processed', False)\
        .limit(limit)\
        .execute()
    return data.data

def mark_posts_processed(post_ids):
    """Mark posts as analyzed"""
    supabase.table('raw_posts')\
        .update({'processed': True})\
        .in_('id', post_ids)\
        .execute()

