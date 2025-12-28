"""
AI Analyzer using Claude API to analyze scraped posts and extract product opportunities
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def analyze_post_for_opportunities(post_content: str, context: dict = None) -> dict:
    """
    Analyze a post to identify product opportunities
    
    Args:
        post_content: The content of the post to analyze
        context: Additional context (metrics, platform, etc.)
    
    Returns:
        Dictionary with opportunity details
    """
    prompt = f"""Analyze the following social media post and identify potential product opportunities or gaps in the market.

Post content: {post_content}
Context: {context or {}}

Identify:
1. Product opportunities mentioned or implied
2. Pain points that could be solved with a product
3. Market gaps or unmet needs
4. Confidence level (0-100) for each opportunity

Return your analysis in a structured format."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return {
            'analysis': message.content[0].text,
            'model': 'claude-3-5-sonnet'
        }
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return {'analysis': '', 'error': str(e)}

def extract_opportunities_from_batch(posts: list) -> list:
    """
    Analyze a batch of posts and extract opportunities
    
    Args:
        posts: List of post dictionaries
    
    Returns:
        List of identified opportunities
    """
    opportunities = []
    
    for post in posts:
        analysis = analyze_post_for_opportunities(
            post.get('content', ''),
            {
                'platform': post.get('platform'),
                'metrics': post.get('metrics', {})
            }
        )
        
        if analysis.get('analysis'):
            opportunities.append({
                'post_id': post.get('id'),
                'analysis': analysis['analysis'],
                'source_content': post.get('content', '')[:200]  # Truncate for storage
            })
    
    return opportunities

