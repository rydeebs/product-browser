"""
AI Analyzer using Claude API to analyze scraped posts and extract product opportunities
"""
import os
import json
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
        Dictionary with structured opportunity details
    """
    metrics = context.get('metrics', {}) if context else {}
    likes = metrics.get('upvotes', 0)
    comments = metrics.get('comments', 0)
    
    prompt = f"""Analyze this social media post for product opportunity:

Content: {post_content}

Engagement: {likes} likes/upvotes, {comments} comments

Extract the following and respond ONLY with valid JSON (no markdown, no explanation):

{{
    "core_problem": "One sentence describing the main problem or pain point",
    "pain_severity": 7,
    "willingness_to_pay": {{
        "likely": true,
        "evidence": "Quote or reasoning from the post"
    }},
    "product_gap_category": "new_invention | better_alternative | cheaper_option | quality_improvement",
    "recommended_product": "2-3 sentence product concept that solves this problem",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "target_audience": "Who would buy this product",
    "confidence_score": 75
}}

Rules:
- pain_severity: 1-10 scale (10 = extreme pain)
- confidence_score: 0-100 (how confident you are this is a real opportunity)
- If no clear opportunity exists, set confidence_score below 30
- product_gap_category must be one of: new_invention, better_alternative, cheaper_option, quality_improvement
- Respond with ONLY the JSON object, nothing else"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = message.content[0].text.strip()
        
        # Try to parse JSON response
        try:
            # Handle potential markdown code blocks
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            parsed = json.loads(response_text)
            parsed['model'] = 'claude-sonnet-4'
            parsed['raw_response'] = False
            return parsed
            
        except json.JSONDecodeError:
            # Fallback: return raw text if JSON parsing fails
            return {
                'analysis': response_text,
                'model': 'claude-sonnet-4',
                'raw_response': True,
                'confidence_score': 0
            }
        
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return {
            'error': str(e),
            'confidence_score': 0,
            'raw_response': True
        }


def analyze_post_simple(post_content: str, context: dict = None) -> dict:
    """
    Simple analysis - returns unstructured text (legacy support)
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
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return {
            'analysis': message.content[0].text,
            'model': 'claude-sonnet-4'
        }
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return {'analysis': '', 'error': str(e)}

def extract_opportunities_from_batch(posts: list, min_confidence: int = 30) -> list:
    """
    Analyze a batch of posts and extract opportunities
    
    Args:
        posts: List of post dictionaries
        min_confidence: Minimum confidence score to include (default 30)
    
    Returns:
        List of identified opportunities with structured data
    """
    opportunities = []
    
    for i, post in enumerate(posts):
        print(f'  Analyzing post {i+1}/{len(posts)}...')
        
        analysis = analyze_post_for_opportunities(
            post.get('content', ''),
            {
                'platform': post.get('platform'),
                'metrics': post.get('metrics', {})
            }
        )
        
        # Skip low-confidence or errored analyses
        confidence = analysis.get('confidence_score', 0)
        if confidence < min_confidence:
            print(f'    ⏭️  Skipped (confidence: {confidence})')
            continue
        
        if analysis.get('error'):
            print(f'    ❌ Error: {analysis["error"]}')
            continue
        
        opportunity = {
            'post_id': post.get('id'),
            'source_content': post.get('content', '')[:500],
            'platform': post.get('platform'),
            'metrics': post.get('metrics', {}),
            # Structured fields from AI
            'core_problem': analysis.get('core_problem', ''),
            'pain_severity': analysis.get('pain_severity', 0),
            'willingness_to_pay': analysis.get('willingness_to_pay', {}),
            'product_gap_category': analysis.get('product_gap_category', ''),
            'recommended_product': analysis.get('recommended_product', ''),
            'keywords': analysis.get('keywords', []),
            'target_audience': analysis.get('target_audience', ''),
            'confidence_score': confidence,
        }
        
        opportunities.append(opportunity)
        print(f'    ✅ Found opportunity (confidence: {confidence}, pain: {analysis.get("pain_severity", 0)})')
    
    return opportunities


def test_analyzer():
    """Test the analyzer with sample posts"""
    sample_posts = [
        {
            'id': 'test_1',
            'platform': 'reddit',
            'content': "I wish there was a water bottle that could track how much I drink. I always forget to stay hydrated and end up with headaches.",
            'metrics': {'upvotes': 234, 'comments': 45}
        },
        {
            'id': 'test_2', 
            'platform': 'reddit',
            'content': "Why isn't there a good app for tracking my pet's medications? I have 3 dogs and always forget who got what.",
            'metrics': {'upvotes': 567, 'comments': 89}
        },
        {
            'id': 'test_3',
            'platform': 'reddit',
            'content': "Just bought a new couch, looks great!",
            'metrics': {'upvotes': 12, 'comments': 3}
        }
    ]
    
    print("🧪 Testing AI Analyzer with sample posts...\n")
    
    for post in sample_posts:
        print(f"📝 Post: {post['content'][:50]}...")
        result = analyze_post_for_opportunities(post['content'], {'metrics': post['metrics']})
        
        if result.get('raw_response'):
            print(f"   ⚠️  Raw response (JSON parsing failed)")
        else:
            print(f"   ✅ Pain: {result.get('pain_severity', 'N/A')}/10")
            print(f"   ✅ Confidence: {result.get('confidence_score', 'N/A')}%")
            print(f"   ✅ Category: {result.get('product_gap_category', 'N/A')}")
            print(f"   ✅ Product: {result.get('recommended_product', 'N/A')[:80]}...")
        print()
    
    print("✅ Test complete!")


if __name__ == '__main__':
    test_analyzer()

