#!/usr/bin/env python3
import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Add parent directory to path for importing modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
cleaned_data_dir = os.path.join(parent_dir, 'cleaned_data')
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visualizations')

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('viridis')

def format_currency(x, pos):
    """Format currency for plot labels"""
    return f'${x:.0f}' if x >= 1 else f'${x:.2f}'

def format_thousands(x, pos):
    """Format large numbers with K, M for plot labels"""
    if x >= 1e6:
        return f'{x/1e6:.1f}M'
    elif x >= 1e3:
        return f'{x/1e3:.1f}K'
    else:
        return f'{x:.0f}'

def load_data():
    """Load cleaned data for analysis"""
    try:
        # Load all data from parquet for efficiency
        all_data_path = os.path.join(cleaned_data_dir, 'all_cleaned_data.parquet')
        if os.path.exists(all_data_path):
            return pd.read_parquet(all_data_path)
        
        # Fallback to CSV if parquet doesn't exist
        all_data_path = os.path.join(cleaned_data_dir, 'all_cleaned_data.csv')
        if os.path.exists(all_data_path):
            return pd.read_csv(all_data_path)
        
        print("No cleaned data found. Please run the data cleaning script first.")
        return None
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return None

def analyze_categories(df):
    """Analyze product distribution across categories"""
    if df is None or df.empty:
        return
    
    # Count products per category and data source
    category_counts = df.groupby(['category', 'data_source']).size().reset_index(name='count')
    pivot_df = category_counts.pivot(index='category', columns='data_source', values='count').fillna(0)
    
    # Plot category distribution
    plt.figure(figsize=(12, 8))
    pivot_df.plot(kind='barh', stacked=True, figsize=(12, 8))
    plt.title('Number of Products by Category and Data Source', fontsize=16)
    plt.xlabel('Number of Products', fontsize=12)
    plt.ylabel('Category', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'category_distribution.png'), dpi=300)
    
    # Plot category pie chart
    plt.figure(figsize=(10, 10))
    category_total = df.groupby('category').size()
    plt.pie(category_total, labels=category_total.index, autopct='%1.1f%%', startangle=90, shadow=True)
    plt.axis('equal')
    plt.title('Share of Products by Category', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'category_pie_chart.png'), dpi=300)
    
    # Save summary data
    category_summary = category_counts.to_dict('records')
    with open(os.path.join(output_dir, 'category_summary.json'), 'w') as f:
        json.dump(category_summary, f, indent=2)

def analyze_pricing(df):
    """Analyze product pricing"""
    if df is None or df.empty or 'price' not in df.columns:
        return
    
    # Remove extreme outliers for better visualization (keep 99th percentile)
    max_price = df['price'].quantile(0.99)
    df_filtered = df[df['price'] <= max_price].copy()
    
    # Price distribution by category
    plt.figure(figsize=(12, 8))
    ax = sns.boxplot(x='category', y='price', data=df_filtered)
    plt.title('Price Distribution by Category', fontsize=16)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Price ($)', fontsize=12)
    plt.xlabel('Category', fontsize=12)
    ax.yaxis.set_major_formatter(FuncFormatter(format_currency))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'price_distribution_by_category.png'), dpi=300)
    
    # Price histogram
    plt.figure(figsize=(12, 6))
    ax = sns.histplot(df_filtered['price'], bins=50, kde=True)
    plt.title('Price Distribution (excluding top 1% outliers)', fontsize=16)
    plt.xlabel('Price ($)', fontsize=12)
    plt.ylabel('Number of Products', fontsize=12)
    ax.xaxis.set_major_formatter(FuncFormatter(format_currency))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'price_histogram.png'), dpi=300)
    
    # Price by data source
    plt.figure(figsize=(10, 6))
    ax = sns.boxplot(x='data_source', y='price', data=df_filtered)
    plt.title('Price Comparison by Data Source', fontsize=16)
    plt.xlabel('Data Source', fontsize=12)
    plt.ylabel('Price ($)', fontsize=12)
    ax.yaxis.set_major_formatter(FuncFormatter(format_currency))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'price_by_data_source.png'), dpi=300)
    
    # Calculate price statistics
    price_stats = {
        'overall': {
            'mean': df['price'].mean(),
            'median': df['price'].median(),
            'min': df['price'].min(),
            'max': df['price'].max(),
            'std': df['price'].std()
        },
        'by_category': df.groupby('category')['price'].agg(['mean', 'median', 'min', 'max', 'std']).to_dict(),
        'by_data_source': df.groupby('data_source')['price'].agg(['mean', 'median', 'min', 'max', 'std']).to_dict()
    }
    
    with open(os.path.join(output_dir, 'price_statistics.json'), 'w') as f:
        json.dump(price_stats, f, indent=2, default=str)

def analyze_ratings(df):
    """Analyze product ratings"""
    if df is None or df.empty or 'rating_value' not in df.columns:
        return
    
    # Rating distribution
    plt.figure(figsize=(10, 6))
    ax = sns.histplot(df['rating_value'].dropna(), bins=20, kde=True)
    plt.title('Rating Distribution', fontsize=16)
    plt.xlabel('Rating (out of 5)', fontsize=12)
    plt.ylabel('Number of Products', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rating_distribution.png'), dpi=300)
    
    # Average rating by category
    plt.figure(figsize=(12, 6))
    category_ratings = df.groupby('category')['rating_value'].mean().sort_values(ascending=False)
    category_ratings.plot(kind='bar', figsize=(12, 6))
    plt.title('Average Rating by Category', fontsize=16)
    plt.xlabel('Category', fontsize=12)
    plt.ylabel('Average Rating', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 5)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'average_rating_by_category.png'), dpi=300)
    
    # Rating vs. price scatterplot
    plt.figure(figsize=(10, 6))
    # Filter outliers for better visualization
    df_filtered = df[(df['price'] <= df['price'].quantile(0.95)) & 
                     (df['rating_value'].notna()) & 
                     (df['review_count_value'] <= df['review_count_value'].quantile(0.95))]
    
    scatter = plt.scatter(df_filtered['price'], 
                          df_filtered['rating_value'], 
                          alpha=0.5,
                          c=df_filtered['review_count_value'],
                          cmap='viridis',
                          s=df_filtered['review_count_value']/100)
    
    plt.colorbar(scatter, label='Number of Reviews')
    plt.title('Price vs. Rating (Size: Number of Reviews)', fontsize=16)
    plt.xlabel('Price ($)', fontsize=12)
    plt.ylabel('Rating (out of 5)', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'price_vs_rating.png'), dpi=300)
    
    # Calculate rating statistics
    rating_stats = {
        'overall': {
            'mean': df['rating_value'].mean(),
            'median': df['rating_value'].median(),
            'min': df['rating_value'].min(),
            'max': df['rating_value'].max(),
            'std': df['rating_value'].std()
        },
        'by_category': df.groupby('category')['rating_value'].agg(['mean', 'median', 'min', 'max', 'std']).to_dict(),
        'by_data_source': df.groupby('data_source')['rating_value'].agg(['mean', 'median', 'min', 'max', 'std']).to_dict()
    }
    
    with open(os.path.join(output_dir, 'rating_statistics.json'), 'w') as f:
        json.dump(rating_stats, f, indent=2, default=str)

def analyze_reviews(df):
    """Analyze product reviews"""
    if df is None or df.empty or 'review_count_value' not in df.columns:
        return
    
    # Filter outliers for better visualization
    df_filtered = df[df['review_count_value'] <= df['review_count_value'].quantile(0.95)]
    
    # Review count distribution
    plt.figure(figsize=(10, 6))
    ax = sns.histplot(df_filtered['review_count_value'].dropna(), bins=50, kde=True)
    plt.title('Review Count Distribution (excluding top 5% outliers)', fontsize=16)
    plt.xlabel('Number of Reviews', fontsize=12)
    plt.ylabel('Number of Products', fontsize=12)
    ax.xaxis.set_major_formatter(FuncFormatter(format_thousands))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'review_count_distribution.png'), dpi=300)
    
    # Average reviews by category
    plt.figure(figsize=(12, 6))
    category_reviews = df.groupby('category')['review_count_value'].mean().sort_values(ascending=False)
    ax = category_reviews.plot(kind='bar', figsize=(12, 6))
    plt.title('Average Number of Reviews by Category', fontsize=16)
    plt.xlabel('Category', fontsize=12)
    plt.ylabel('Average Number of Reviews', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    ax.yaxis.set_major_formatter(FuncFormatter(format_thousands))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'average_reviews_by_category.png'), dpi=300)
    
    # Reviews vs. ratings heatmap
    plt.figure(figsize=(10, 8))
    
    # Create rating and review count bins
    df['rating_bin'] = pd.cut(df['rating_value'], bins=np.arange(1, 5.5, 0.5))
    df['review_bin'] = pd.cut(df['review_count_value'], 
                              bins=[0, 10, 100, 1000, 10000, df['review_count_value'].max()],
                              labels=['<10', '10-100', '100-1K', '1K-10K', '>10K'])
    
    # Create a contingency table
    heatmap_data = pd.crosstab(df['rating_bin'], df['review_bin'])
    
    # Plot heatmap
    sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlGnBu')
    plt.title('Number of Products by Rating and Review Count', fontsize=16)
    plt.xlabel('Number of Reviews', fontsize=12)
    plt.ylabel('Rating Range', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rating_review_heatmap.png'), dpi=300)
    
    # Calculate review statistics
    review_stats = {
        'overall': {
            'mean': df['review_count_value'].mean(),
            'median': df['review_count_value'].median(),
            'min': df['review_count_value'].min(),
            'max': df['review_count_value'].max(),
            'std': df['review_count_value'].std(),
            'total': df['review_count_value'].sum()
        },
        'by_category': df.groupby('category')['review_count_value'].agg(['mean', 'median', 'min', 'max', 'std', 'sum']).to_dict(),
        'by_data_source': df.groupby('data_source')['review_count_value'].agg(['mean', 'median', 'min', 'max', 'std', 'sum']).to_dict()
    }
    
    with open(os.path.join(output_dir, 'review_statistics.json'), 'w') as f:
        json.dump(review_stats, f, indent=2, default=str)

def analyze_top_products(df):
    """Analyze top products by various metrics"""
    if df is None or df.empty:
        return
    
    # Top 20 products by review count
    top_by_reviews = df.sort_values('review_count_value', ascending=False).head(20)[
        ['product_name', 'category', 'price', 'rating_value', 'review_count_value', 'data_source', 'clean_product_id']
    ]
    
    # Top 20 products by rating (with at least 100 reviews)
    top_by_rating = df[df['review_count_value'] >= 100].sort_values('rating_value', ascending=False).head(20)[
        ['product_name', 'category', 'price', 'rating_value', 'review_count_value', 'data_source', 'clean_product_id']
    ]
    
    # Top 20 most expensive products
    top_by_price = df.sort_values('price', ascending=False).head(20)[
        ['product_name', 'category', 'price', 'rating_value', 'review_count_value', 'data_source', 'clean_product_id']
    ]
    
    # Visualize top products by reviews
    plt.figure(figsize=(14, 10))
    ax = sns.barplot(x='review_count_value', y='product_name', data=top_by_reviews.head(10))
    plt.title('Top 10 Products by Number of Reviews', fontsize=16)
    plt.xlabel('Number of Reviews', fontsize=12)
    plt.ylabel('Product', fontsize=12)
    ax.xaxis.set_major_formatter(FuncFormatter(format_thousands))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'top_products_by_reviews.png'), dpi=300)
    
    # Save results to JSON
    top_products = {
        'by_reviews': top_by_reviews.to_dict('records'),
        'by_rating': top_by_rating.to_dict('records'),
        'by_price': top_by_price.to_dict('records')
    }
    
    with open(os.path.join(output_dir, 'top_products.json'), 'w') as f:
        json.dump(top_products, f, indent=2, default=str)

def analyze_prime_status(df):
    """Analyze products with Prime status"""
    if df is None or df.empty or 'is_prime' not in df.columns:
        return
    
    # Count prime vs non-prime products
    prime_counts = df['is_prime'].value_counts()
    
    # Plot pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(prime_counts, labels=['Non-Prime', 'Prime'] if prime_counts.index[0] == False else ['Prime', 'Non-Prime'],
            autopct='%1.1f%%', startangle=90, shadow=True, colors=['#ff9999', '#66b3ff'])
    plt.axis('equal')
    plt.title('Prime vs Non-Prime Products', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'prime_distribution.png'), dpi=300)
    
    # Prime status by category
    prime_by_category = df.groupby('category')['is_prime'].mean().sort_values(ascending=False)
    
    plt.figure(figsize=(12, 6))
    prime_by_category.plot(kind='bar', figsize=(12, 6))
    plt.title('Percentage of Prime Products by Category', fontsize=16)
    plt.xlabel('Category', fontsize=12)
    plt.ylabel('Percentage of Prime Products', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 1)
    # Format y-axis as percentage
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.0%}'))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'prime_by_category.png'), dpi=300)
    
    # Price comparison: Prime vs Non-Prime
    plt.figure(figsize=(10, 6))
    # Filter outliers for better visualization
    df_filtered = df[df['price'] <= df['price'].quantile(0.95)]
    
    ax = sns.boxplot(x='is_prime', y='price', data=df_filtered)
    plt.title('Price Comparison: Prime vs Non-Prime Products', fontsize=16)
    plt.xlabel('Prime Status', fontsize=12)
    plt.ylabel('Price ($)', fontsize=12)
    plt.xticks([0, 1], ['Non-Prime', 'Prime'])
    ax.yaxis.set_major_formatter(FuncFormatter(format_currency))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'prime_price_comparison.png'), dpi=300)
    
    # Calculate prime statistics
    prime_stats = {
        'overall': {
            'prime_count': int(df['is_prime'].sum()),
            'non_prime_count': int((~df['is_prime']).sum()),
            'prime_percentage': float(df['is_prime'].mean())
        },
        'by_category': {cat: float(pct) for cat, pct in prime_by_category.items()},
        'price_comparison': {
            'prime_avg_price': float(df[df['is_prime']]['price'].mean()),
            'non_prime_avg_price': float(df[~df['is_prime']]['price'].mean()),
            'prime_median_price': float(df[df['is_prime']]['price'].median()),
            'non_prime_median_price': float(df[~df['is_prime']]['price'].median())
        }
    }
    
    with open(os.path.join(output_dir, 'prime_statistics.json'), 'w') as f:
        json.dump(prime_stats, f, indent=2)

def generate_summary():
    """Generate a summary of the exploratory analysis"""
    # Combine all JSON statistics into one summary file
    summary = {}
    
    json_files = [
        'category_summary.json',
        'price_statistics.json',
        'rating_statistics.json',
        'review_statistics.json',
        'prime_statistics.json'
    ]
    
    for json_file in json_files:
        file_path = os.path.join(output_dir, json_file)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                summary[json_file.replace('_statistics.json', '').replace('_summary.json', '')] = data
    
    # Add list of visualizations
    summary['visualizations'] = [f for f in os.listdir(output_dir) if f.endswith('.png')]
    
    # Save the complete summary
    with open(os.path.join(output_dir, 'eda_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2, default=str)

def main():
    print("Starting exploratory data analysis...")
    
    # Load data
    df = load_data()
    if df is None:
        print("No data available for analysis. Exiting.")
        return
    
    print(f"Loaded data with {len(df)} rows and {df.columns.size} columns")
    
    # Perform analyses
    analyze_categories(df)
    print("Completed category analysis")
    
    analyze_pricing(df)
    print("Completed pricing analysis")
    
    analyze_ratings(df)
    print("Completed ratings analysis")
    
    analyze_reviews(df)
    print("Completed reviews analysis")
    
    analyze_top_products(df)
    print("Completed top products analysis")
    
    analyze_prime_status(df)
    print("Completed Prime status analysis")
    
    # Generate summary
    generate_summary()
    print("Generated analysis summary")
    
    print(f"Exploratory data analysis complete. Visualizations saved to {output_dir}")

if __name__ == "__main__":
    main() 