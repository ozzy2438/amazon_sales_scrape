#!/usr/bin/env python3
import json
import os
import re
import pandas as pd
import numpy as np
from datetime import datetime

# Set paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cleaned_data')

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_json_data(file_path):
    """Load JSON data from file path"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return None

def extract_numeric_value(value_str):
    """Extract numeric value from string (e.g., '$10.99' -> 10.99)"""
    if not value_str or not isinstance(value_str, str):
        return None
    
    # Extract numbers with decimal points
    match = re.search(r'[\d,]+\.?\d*', value_str)
    if match:
        # Remove commas and convert to float
        return float(match.group().replace(',', ''))
    return None

def extract_rating(rating_str):
    """Extract numeric rating from string (e.g., '4.5 out of 5 stars' -> 4.5)"""
    if not rating_str or not isinstance(rating_str, str):
        return None
    
    match = re.search(r'(\d+\.\d+|\d+)', rating_str)
    if match:
        return float(match.group())
    return None

def extract_review_count(review_count_str):
    """Extract numeric review count from string (e.g., '1,234' -> 1234)"""
    if not review_count_str or not isinstance(review_count_str, str):
        return None
    
    match = re.search(r'[\d,]+', review_count_str)
    if match:
        return int(match.group().replace(',', ''))
    return None

def extract_product_id(product_id_str):
    """Extract the actual product ID from the URL or ID string"""
    if not product_id_str or not isinstance(product_id_str, str):
        return None
    
    # Try to extract the product ID in the format B0XXXXX
    match = re.search(r'/dp/([A-Z0-9]{10})(?:/|$|\?)', product_id_str)
    if match:
        return match.group(1)
    return product_id_str

def clean_bestsellers_data(data):
    """Clean bestsellers data"""
    all_products = []
    
    for category, products in data.items():
        # Filter out duplicates and incomplete entries
        unique_products = {}
        
        for product in products:
            # Skip entries without a product name or with the session ID as product name
            if not product.get('product_name') or re.match(r'\d+\s+\d+\s+\d+', product.get('product_name', '')):
                continue
                
            # Extract product ID
            product_id = extract_product_id(product.get('product_id', product.get('product_link', '')))
            
            if not product_id:
                continue
                
            # Only keep the most complete record for each product ID
            if product_id not in unique_products or len(product) > len(unique_products[product_id]):
                product['clean_product_id'] = product_id
                unique_products[product_id] = product
        
        # Convert to list and add category
        for product_id, product in unique_products.items():
            product['category'] = category
            all_products.append(product)
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(all_products)
    
    # Clean and convert price columns
    if 'discounted_price' in df.columns:
        df['price'] = df['discounted_price'].apply(extract_numeric_value)
    
    if 'actual_price' in df.columns:
        df['original_price'] = df['actual_price'].apply(extract_numeric_value)
    
    # Calculate discount percentage
    if 'original_price' in df.columns and 'price' in df.columns:
        df['discount_percent'] = np.where(
            (df['original_price'].notna()) & (df['price'].notna()) & (df['original_price'] > 0),
            ((df['original_price'] - df['price']) / df['original_price'] * 100).round(2),
            None
        )
    
    # Clean rating and review count
    if 'rating' in df.columns:
        df['rating_value'] = df['rating'].apply(extract_rating)
    
    if 'review_count' in df.columns:
        df['review_count_value'] = df['review_count'].apply(extract_review_count)
    
    # Add data source and timestamp
    df['data_source'] = 'bestsellers'
    df['processed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return df

def clean_trends_data(data):
    """Clean trends data"""
    all_products = []
    
    for category, products in data.items():
        # Filter out duplicates and incomplete entries
        unique_products = {}
        
        for product in products:
            # Skip entries without a product name or with the session ID as product name
            if not product.get('product_name') or re.match(r'\d+\s+\d+\s+\d+', product.get('product_name', '')):
                continue
                
            # Extract product ID
            product_id = extract_product_id(product.get('product_id', product.get('product_link', '')))
            
            if not product_id:
                continue
                
            # Only keep the most complete record for each product ID
            if product_id not in unique_products or len(product) > len(unique_products[product_id]):
                product['clean_product_id'] = product_id
                unique_products[product_id] = product
        
        # Convert to list and add category
        for product_id, product in unique_products.items():
            product['category'] = category
            all_products.append(product)
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(all_products)
    
    # Clean and convert price columns
    if 'discounted_price' in df.columns:
        df['price'] = df['discounted_price'].apply(extract_numeric_value)
    
    if 'actual_price' in df.columns:
        df['original_price'] = df['actual_price'].apply(extract_numeric_value)
    
    # Extract percent change
    if 'percent_change' in df.columns:
        df['percent_change_value'] = df['percent_change'].apply(
            lambda x: extract_numeric_value(x) if x and isinstance(x, str) else None
        )
    
    # Calculate discount percentage
    if 'original_price' in df.columns and 'price' in df.columns:
        df['discount_percent'] = np.where(
            (df['original_price'].notna()) & (df['price'].notna()) & (df['original_price'] > 0),
            ((df['original_price'] - df['price']) / df['original_price'] * 100).round(2),
            None
        )
    
    # Clean rating and review count
    if 'rating' in df.columns:
        df['rating_value'] = df['rating'].apply(extract_rating)
    
    if 'review_count' in df.columns:
        df['review_count_value'] = df['review_count'].apply(extract_review_count)
    
    # Add data source and timestamp
    df['data_source'] = 'trends'
    df['processed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return df

def clean_new_releases_data(data):
    """Clean new releases data"""
    all_products = []
    
    for category, products in data.items():
        # Filter out duplicates and incomplete entries
        unique_products = {}
        
        for product in products:
            # Skip entries without a product name or with the session ID as product name
            if not product.get('product_name') or re.match(r'\d+\s+\d+\s+\d+', product.get('product_name', '')):
                continue
                
            # Extract product ID
            product_id = extract_product_id(product.get('product_id', product.get('product_link', '')))
            
            if not product_id:
                continue
                
            # Only keep the most complete record for each product ID
            if product_id not in unique_products or len(product) > len(unique_products[product_id]):
                product['clean_product_id'] = product_id
                unique_products[product_id] = product
        
        # Convert to list and add category
        for product_id, product in unique_products.items():
            product['category'] = category
            all_products.append(product)
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(all_products)
    
    # Clean and convert price columns
    if 'discounted_price' in df.columns:
        df['price'] = df['discounted_price'].apply(extract_numeric_value)
    
    if 'actual_price' in df.columns:
        df['original_price'] = df['actual_price'].apply(extract_numeric_value)
    
    # Calculate discount percentage
    if 'original_price' in df.columns and 'price' in df.columns:
        df['discount_percent'] = np.where(
            (df['original_price'].notna()) & (df['price'].notna()) & (df['original_price'] > 0),
            ((df['original_price'] - df['price']) / df['original_price'] * 100).round(2),
            None
        )
    
    # Clean rating and review count
    if 'rating' in df.columns:
        df['rating_value'] = df['rating'].apply(extract_rating)
    
    if 'review_count' in df.columns:
        df['review_count_value'] = df['review_count'].apply(extract_review_count)
    
    # Add data source and timestamp
    df['data_source'] = 'new_releases'
    df['processed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return df

def main():
    print("Starting data cleaning process...")
    
    # Load data
    bestsellers_path = os.path.join(BASE_DIR, 'amazon_bestsellers.json')
    trends_path = os.path.join(BASE_DIR, 'amazon_trends.json')
    new_releases_path = os.path.join(BASE_DIR, 'amazon_new_releases.json')
    
    bestsellers_data = load_json_data(bestsellers_path)
    trends_data = load_json_data(trends_path)
    new_releases_data = load_json_data(new_releases_path)
    
    # Clean data
    cleaned_bestsellers = clean_bestsellers_data(bestsellers_data) if bestsellers_data else pd.DataFrame()
    cleaned_trends = clean_trends_data(trends_data) if trends_data else pd.DataFrame()
    cleaned_new_releases = clean_new_releases_data(new_releases_data) if new_releases_data else pd.DataFrame()
    
    # Combine all data sources
    all_data = pd.concat([cleaned_bestsellers, cleaned_trends, cleaned_new_releases], ignore_index=True)
    
    # Final cleaning and feature engineering
    
    # Standardize boolean fields
    if 'is_prime' in all_data.columns:
        all_data['is_prime'] = all_data['is_prime'].fillna(False)
    
    # Save cleaned data
    bestsellers_output = os.path.join(OUTPUT_DIR, 'cleaned_bestsellers.csv')
    trends_output = os.path.join(OUTPUT_DIR, 'cleaned_trends.csv')
    new_releases_output = os.path.join(OUTPUT_DIR, 'cleaned_new_releases.csv')
    all_data_output = os.path.join(OUTPUT_DIR, 'all_cleaned_data.csv')
    
    print(f"Saving cleaned data to {OUTPUT_DIR}...")
    
    cleaned_bestsellers.to_csv(bestsellers_output, index=False)
    cleaned_trends.to_csv(trends_output, index=False)
    cleaned_new_releases.to_csv(new_releases_output, index=False)
    all_data.to_csv(all_data_output, index=False)
    
    # Save a version to Parquet for more efficient data processing
    all_data.to_parquet(os.path.join(OUTPUT_DIR, 'all_cleaned_data.parquet'))
    
    # Save data summary
    summary = {
        "total_products": len(all_data),
        "unique_products": all_data['clean_product_id'].nunique(),
        "bestsellers_count": len(cleaned_bestsellers),
        "trends_count": len(cleaned_trends),
        "new_releases_count": len(cleaned_new_releases),
        "categories": all_data['category'].unique().tolist(),
        "processed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(os.path.join(OUTPUT_DIR, 'data_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print("Data cleaning complete!")
    print(f"Processed {summary['total_products']} products across {len(summary['categories'])} categories")
    print(f"Found {summary['unique_products']} unique products")

if __name__ == "__main__":
    main() 