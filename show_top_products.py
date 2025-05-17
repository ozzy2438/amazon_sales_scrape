#!/usr/bin/env python
import json

def extract_asin(product_id):
    # ASIN genellikle URL içindeki /dp/ kısmından sonra gelir
    if not product_id:
        return "Unknown"
    
    parts = product_id.split('/')
    for i, part in enumerate(parts):
        if part == 'dp' and i+1 < len(parts):
            return parts[i+1]
    
    return "Unknown"

def main():
    try:
        # Bestsellers verilerini oku
        with open('amazon_bestsellers.json', 'r', encoding='utf-8') as f:
            bestsellers = json.load(f)
            
        print("=== AMAZON BESTSELLERS ===")
        
        for category, products in bestsellers.items():
            print(f"\n{category.upper()} - Top 5 Products:")
            
            for i, product in enumerate(products[:5], 1):
                asin = extract_asin(product.get('product_id', ''))
                name = product.get('product_name', 'Unknown Product')
                price = product.get('discounted_price', 'N/A')
                rating = product.get('rating', 'N/A')
                reviews = product.get('review_count', 'N/A')
                
                print(f"{i}. {name}")
                print(f"   Price: {price} | ASIN: {asin} | Rating: {rating} | Reviews: {reviews}")
        
        # Trends verilerini oku
        with open('amazon_trends.json', 'r', encoding='utf-8') as f:
            trends = json.load(f)
            
        print("\n\n=== AMAZON TRENDING PRODUCTS ===")
        
        for category, products in trends.items():
            print(f"\n{category.upper()} - Top 5 Trending Products:")
            
            for i, product in enumerate(products[:5], 1):
                asin = extract_asin(product.get('product_id', ''))
                name = product.get('product_name', 'Unknown Product')
                price = product.get('discounted_price', 'N/A')
                percent_change = product.get('percent_change', 'N/A')
                
                print(f"{i}. {name}")
                print(f"   Price: {price} | ASIN: {asin} | Change: {percent_change}")
        
        # New Releases verilerini oku
        with open('amazon_new_releases.json', 'r', encoding='utf-8') as f:
            new_releases = json.load(f)
            
        print("\n\n=== AMAZON NEW RELEASES ===")
        
        for category, products in new_releases.items():
            print(f"\n{category.upper()} - Top 5 New Releases:")
            
            for i, product in enumerate(products[:5], 1):
                asin = extract_asin(product.get('product_id', ''))
                name = product.get('product_name', 'Unknown Product')
                price = product.get('discounted_price', 'N/A')
                release_date = product.get('release_date', 'N/A')
                
                print(f"{i}. {name}")
                print(f"   Price: {price} | ASIN: {asin} | Release Date: {release_date}")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 