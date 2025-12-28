"""
Amazon scraper for competitor analysis
"""
import requests
from bs4 import BeautifulSoup
import time
import random

def search_amazon_products(keywords: str, max_results: int = 10) -> list:
    """
    Search Amazon for products matching keywords
    
    Args:
        keywords: Search keywords
        max_results: Maximum number of results to return
    
    Returns:
        List of product dictionaries
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    # Amazon search URL
    url = f"https://www.amazon.com/s?k={keywords.replace(' ', '+')}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = []
        
        # Extract product information (Amazon's HTML structure may vary)
        product_elements = soup.find_all('div', {'data-component-type': 's-search-result'})[:max_results]
        
        for element in product_elements:
            try:
                title_elem = element.find('h2', class_='a-size-mini')
                price_elem = element.find('span', class_='a-price-whole')
                rating_elem = element.find('span', class_='a-icon-alt')
                link_elem = element.find('a', class_='a-link-normal')
                
                if title_elem:
                    products.append({
                        'title': title_elem.get_text(strip=True),
                        'price': price_elem.get_text(strip=True) if price_elem else 'N/A',
                        'rating': rating_elem.get_text(strip=True) if rating_elem else 'N/A',
                        'url': f"https://www.amazon.com{link_elem['href']}" if link_elem else None
                    })
            except Exception as e:
                print(f"Error parsing product: {e}")
                continue
        
        # Add delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        return products
    except Exception as e:
        print(f"Error scraping Amazon: {e}")
        return []

def analyze_competitor_landscape(keywords: list) -> dict:
    """
    Analyze competitor landscape for given keywords
    
    Args:
        keywords: List of keywords to search
    
    Returns:
        Dictionary with competitor analysis
    """
    all_products = []
    
    for keyword in keywords:
        products = search_amazon_products(keyword)
        all_products.extend(products)
        time.sleep(2)  # Rate limiting
    
    return {
        'total_products': len(all_products),
        'products': all_products[:20],  # Limit to top 20
        'keywords_searched': keywords
    }

