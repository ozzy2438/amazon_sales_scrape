#!/usr/bin/env python3
import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from scipy import stats
from matplotlib.ticker import FuncFormatter

# Add parent directory to path for importing modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
cleaned_data_dir = os.path.join(parent_dir, 'cleaned_data')
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('viridis')

def format_currency(x, pos):
    """Format currency for plot labels"""
    return f'${x:.0f}' if x >= 1 else f'${x:.2f}'

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

def price_segmentation_analysis(df):
    """
    Perform price segmentation analysis to identify different pricing tiers
    """
    if df is None or df.empty or 'price' not in df.columns:
        return None
    
    # Filter out rows with missing price
    df_filtered = df.dropna(subset=['price']).copy()
    
    # Remove extreme outliers (keep 99th percentile)
    max_price = df_filtered['price'].quantile(0.99)
    df_filtered = df_filtered[df_filtered['price'] <= max_price]
    
    # Prepare data for clustering
    price_data = df_filtered[['price']].values
    
    # Scale the data
    scaler = StandardScaler()
    price_data_scaled = scaler.fit_transform(price_data)
    
    # Determine optimal number of clusters (2-10)
    silhouette_scores = []
    k_range = range(2, 11)
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(price_data_scaled)
        silhouette_avg = silhouette_score(price_data_scaled, cluster_labels)
        silhouette_scores.append(silhouette_avg)
    
    # Find optimal K (number of clusters)
    optimal_k = k_range[np.argmax(silhouette_scores)]
    
    # Perform KMeans clustering with optimal K
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    df_filtered['price_segment'] = kmeans.fit_predict(price_data_scaled)
    
    # Extract cluster centers (in original scale)
    centers = scaler.inverse_transform(kmeans.cluster_centers_)
    
    # Sort segments by price (low to high)
    segment_order = df_filtered.groupby('price_segment')['price'].mean().sort_values().index
    segment_map = {old: new for new, old in enumerate(segment_order)}
    df_filtered['price_segment'] = df_filtered['price_segment'].map(segment_map)
    
    # Rename segments to meaningful labels
    segment_labels = ['Budget', 'Economy', 'Mid-range', 'Premium', 'Luxury'][:optimal_k]
    segment_center_map = {i: {'center': centers[segment_order[i]][0], 'label': segment_labels[i]} 
                          for i in range(optimal_k)}
    
    # Add segment labels
    df_filtered['price_segment_label'] = df_filtered['price_segment'].map(lambda x: segment_labels[x])
    
    # Visualize price segments
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='price_segment_label', y='price', data=df_filtered)
    plt.title('Price Segments Identified by Clustering', fontsize=16)
    plt.xlabel('Price Segment', fontsize=12)
    plt.ylabel('Price ($)', fontsize=12)
    plt.gca().yaxis.set_major_formatter(FuncFormatter(format_currency))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'price_segments.png'), dpi=300)
    
    # Create segment profile with simpler calculations to avoid MultiIndex
    segment_profile = {}
    for segment in segment_labels:
        segment_data = df_filtered[df_filtered['price_segment_label'] == segment]
        segment_profile[segment] = {
            'count': len(segment_data),
            'price_mean': segment_data['price'].mean(),
            'price_median': segment_data['price'].median(),
            'price_min': segment_data['price'].min(),
            'price_max': segment_data['price'].max(),
            'price_std': segment_data['price'].std(),
            'rating_mean': segment_data['rating_value'].mean() if 'rating_value' in segment_data.columns else None,
            'rating_count': segment_data['rating_value'].count() if 'rating_value' in segment_data.columns else 0,
            'review_mean': segment_data['review_count_value'].mean() if 'review_count_value' in segment_data.columns else None,
            'review_sum': segment_data['review_count_value'].sum() if 'review_count_value' in segment_data.columns else 0
        }
    
    # Segment distribution by category using a simpler approach
    segment_by_category = {}
    for category in df_filtered['category'].unique():
        category_data = df_filtered[df_filtered['category'] == category]
        total_count = len(category_data)
        if total_count > 0:
            segment_by_category[category] = {}
            for segment in segment_labels:
                segment_count = len(category_data[category_data['price_segment_label'] == segment])
                segment_by_category[category][segment] = segment_count / total_count
    
    # Save results
    segment_results = {
        'optimal_clusters': optimal_k,
        'silhouette_scores': {str(k): float(score) for k, score in zip(k_range, silhouette_scores)},
        'segment_centers': {label: float(segment_center_map[i]['center']) for i, label in enumerate(segment_labels[:optimal_k])},
        'segment_distribution': df_filtered['price_segment_label'].value_counts().to_dict(),
        'segment_stats': segment_profile,
        'segment_by_category': segment_by_category
    }
    
    with open(os.path.join(output_dir, 'price_segmentation.json'), 'w') as f:
        json.dump(segment_results, f, indent=2, default=str)
    
    return df_filtered

def price_elasticity_analysis(df):
    """
    Analyze the relationship between price, ratings, and review counts
    to understand price elasticity of demand
    """
    if df is None or df.empty or 'price' not in df.columns:
        return
    
    # Filter data to include only entries with price, rating, and review count
    df_filtered = df.dropna(subset=['price', 'rating_value', 'review_count_value']).copy()
    
    # Remove outliers
    df_filtered = df_filtered[
        (df_filtered['price'] <= df_filtered['price'].quantile(0.99)) &
        (df_filtered['review_count_value'] <= df_filtered['review_count_value'].quantile(0.99))
    ]
    
    # Calculate correlation between price and review count
    price_review_corr = df_filtered['price'].corr(df_filtered['review_count_value'])
    
    # Calculate correlation between price and rating
    price_rating_corr = df_filtered['price'].corr(df_filtered['rating_value'])
    
    # Regression analysis for price vs review count
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df_filtered['price'], df_filtered['review_count_value']
    )
    
    # Visualization: Price vs Reviews scatterplot with regression line
    plt.figure(figsize=(10, 6))
    sns.regplot(x='price', y='review_count_value', data=df_filtered, scatter_kws={'alpha':0.3}, line_kws={'color':'red'})
    plt.title(f'Price vs. Number of Reviews (r={r_value:.2f}, p={p_value:.4f})', fontsize=16)
    plt.xlabel('Price ($)', fontsize=12)
    plt.ylabel('Number of Reviews', fontsize=12)
    plt.gca().xaxis.set_major_formatter(FuncFormatter(format_currency))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'price_vs_reviews.png'), dpi=300)
    
    # Visualization: Price vs Rating
    plt.figure(figsize=(10, 6))
    slope2, intercept2, r_value2, p_value2, std_err2 = stats.linregress(
        df_filtered['price'], df_filtered['rating_value']
    )
    sns.regplot(x='price', y='rating_value', data=df_filtered, scatter_kws={'alpha':0.3}, line_kws={'color':'red'})
    plt.title(f'Price vs. Rating (r={r_value2:.2f}, p={p_value2:.4f})', fontsize=16)
    plt.xlabel('Price ($)', fontsize=12)
    plt.ylabel('Rating (out of 5)', fontsize=12)
    plt.gca().xaxis.set_major_formatter(FuncFormatter(format_currency))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'price_vs_rating_regression.png'), dpi=300)
    
    # Analyze by category
    category_elasticity = []
    
    for category, group in df_filtered.groupby('category'):
        if len(group) < 10:  # Skip categories with too few products
            continue
            
        # Price vs Reviews correlation and regression
        cat_price_review_corr = group['price'].corr(group['review_count_value'])
        cat_slope, cat_intercept, cat_r_value, cat_p_value, cat_std_err = stats.linregress(
            group['price'], group['review_count_value']
        )
        
        # Price vs Rating correlation and regression
        cat_price_rating_corr = group['price'].corr(group['rating_value'])
        cat_slope2, cat_intercept2, cat_r_value2, cat_p_value2, cat_std_err2 = stats.linregress(
            group['price'], group['rating_value']
        )
        
        category_elasticity.append({
            'category': category,
            'count': len(group),
            'price_review_correlation': cat_price_review_corr,
            'price_review_r_squared': cat_r_value**2,
            'price_review_p_value': cat_p_value,
            'price_review_slope': cat_slope,
            'price_rating_correlation': cat_price_rating_corr,
            'price_rating_r_squared': cat_r_value2**2,
            'price_rating_p_value': cat_p_value2,
            'price_rating_slope': cat_slope2
        })
    
    # Plot top categories by elasticity
    category_df = pd.DataFrame(category_elasticity)
    if not category_df.empty:
        # Sort by absolute correlation value
        top_categories = category_df.sort_values('price_review_correlation', key=abs, ascending=False).head(10)
        
        plt.figure(figsize=(12, 8))
        ax = sns.barplot(x='price_review_correlation', y='category', data=top_categories)
        plt.title('Price-Review Correlation by Category (Top 10)', fontsize=16)
        plt.xlabel('Correlation Coefficient', fontsize=12)
        plt.ylabel('Category', fontsize=12)
        plt.axvline(x=0, color='red', linestyle='--')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'price_elasticity_by_category.png'), dpi=300)
    
    # Save elasticity results
    elasticity_results = {
        'overall': {
            'price_review_correlation': float(price_review_corr),
            'price_review_r_squared': float(r_value**2),
            'price_review_p_value': float(p_value),
            'price_review_slope': float(slope),
            'price_rating_correlation': float(price_rating_corr),
            'price_rating_r_squared': float(r_value2**2),
            'price_rating_p_value': float(p_value2),
            'price_rating_slope': float(slope2)
        },
        'by_category': category_elasticity
    }
    
    with open(os.path.join(output_dir, 'price_elasticity.json'), 'w') as f:
        json.dump(elasticity_results, f, indent=2, default=str)

def competitive_analysis(df):
    """
    Analyze competitive landscape across categories
    """
    if df is None or df.empty:
        return
    
    # Calculate market concentration by category
    category_concentration = []
    
    for category, group in df.groupby('category'):
        if len(group) < 5:  # Skip categories with too few products
            continue
        
        # Count products by category
        product_count = len(group)
        
        # Count unique product IDs
        unique_products = group['clean_product_id'].nunique()
        
        # Calculate HHI (Herfindahl-Hirschman Index) based on review counts
        # This is a simplified version using review counts as proxy for market share
        if 'review_count_value' in group.columns:
            total_reviews = group['review_count_value'].sum()
            if total_reviews > 0:
                shares = group.groupby('clean_product_id')['review_count_value'].sum() / total_reviews
                hhi = (shares ** 2).sum() * 10000  # Scale to 0-10000
            else:
                hhi = None
        else:
            hhi = None
        
        # Calculate average price
        avg_price = group['price'].mean() if 'price' in group.columns else None
        
        # Calculate price range and coefficient of variation
        if 'price' in group.columns:
            price_range = group['price'].max() - group['price'].min()
            price_cv = group['price'].std() / group['price'].mean() if group['price'].mean() > 0 else None
        else:
            price_range = None
            price_cv = None
        
        category_concentration.append({
            'category': category,
            'product_count': product_count,
            'unique_products': unique_products,
            'hhi': hhi,
            'avg_price': avg_price,
            'price_range': price_range,
            'price_cv': price_cv
        })
    
    # Convert to DataFrame for visualization
    concentration_df = pd.DataFrame(category_concentration)
    
    if not concentration_df.empty:
        # Plot HHI by category
        plt.figure(figsize=(12, 8))
        concentration_df_sorted = concentration_df.sort_values('hhi', ascending=False)
        ax = sns.barplot(x='hhi', y='category', data=concentration_df_sorted.head(10))
        plt.title('Market Concentration by Category (Top 10)', fontsize=16)
        plt.xlabel('HHI (Herfindahl-Hirschman Index)', fontsize=12)
        plt.ylabel('Category', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'market_concentration.png'), dpi=300)
        
        # Plot price variation by category
        plt.figure(figsize=(12, 8))
        price_variation_df = concentration_df.sort_values('price_cv', ascending=False)
        ax = sns.barplot(x='price_cv', y='category', data=price_variation_df.head(10))
        plt.title('Price Variation by Category (Top 10)', fontsize=16)
        plt.xlabel('Price Coefficient of Variation', fontsize=12)
        plt.ylabel('Category', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'price_variation_by_category.png'), dpi=300)
    
    # Save competitive analysis results
    competitive_results = {
        'category_concentration': concentration_df.to_dict('records')
    }
    
    with open(os.path.join(output_dir, 'competitive_analysis.json'), 'w') as f:
        json.dump(competitive_results, f, indent=2, default=str)

def perform_trend_analysis(df):
    """
    Analyze trends in the data, comparing bestsellers, new releases, and movers & shakers
    """
    if df is None or df.empty or 'data_source' not in df.columns:
        return
    
    # Calculate key metrics by data source using simpler approach
    source_comparison = {}
    for source, group in df.groupby('data_source'):
        source_comparison[source] = {
            'price_mean': group['price'].mean() if 'price' in group.columns else None,
            'price_median': group['price'].median() if 'price' in group.columns else None,
            'price_std': group['price'].std() if 'price' in group.columns else None,
            'rating_mean': group['rating_value'].mean() if 'rating_value' in group.columns else None,
            'rating_count': group['rating_value'].count() if 'rating_value' in group.columns else 0,
            'review_mean': group['review_count_value'].mean() if 'review_count_value' in group.columns else None,
            'review_sum': group['review_count_value'].sum() if 'review_count_value' in group.columns else 0,
            'unique_products': group['clean_product_id'].nunique() if 'clean_product_id' in group.columns else 0
        }
    
    # Plot price comparison across data sources
    plt.figure(figsize=(10, 6))
    ax = sns.boxplot(x='data_source', y='price', data=df[df['price'] <= df['price'].quantile(0.99)])
    plt.title('Price Distribution by Data Source', fontsize=16)
    plt.xlabel('Data Source', fontsize=12)
    plt.ylabel('Price ($)', fontsize=12)
    ax.yaxis.set_major_formatter(FuncFormatter(format_currency))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'price_by_data_source_comparison.png'), dpi=300)
    
    # Plot rating comparison across data sources
    plt.figure(figsize=(10, 6))
    rating_by_source = df.groupby('data_source')['rating_value'].mean().reset_index()
    ax = sns.barplot(x='data_source', y='rating_value', data=rating_by_source)
    plt.title('Average Rating by Data Source', fontsize=16)
    plt.xlabel('Data Source', fontsize=12)
    plt.ylabel('Average Rating', fontsize=12)
    plt.ylim(0, 5)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rating_by_data_source.png'), dpi=300)
    
    # Analysis of overlap between data sources
    source_groups = df.groupby('data_source')['clean_product_id'].apply(set)
    overlap_analysis = {}
    
    if len(source_groups) > 1:
        source_names = list(source_groups.index)
        for i, src1 in enumerate(source_names):
            for j, src2 in enumerate(source_names):
                if i < j:
                    intersection = source_groups[src1].intersection(source_groups[src2])
                    key = f"{src1}_and_{src2}"
                    overlap_analysis[key] = {
                        "overlap_count": len(intersection),
                        "percentage_of_source1": len(intersection) / len(source_groups[src1]) * 100 if len(source_groups[src1]) > 0 else 0,
                        "percentage_of_source2": len(intersection) / len(source_groups[src2]) * 100 if len(source_groups[src2]) > 0 else 0,
                        "product_ids": list(intersection)[:10]  # Limit to first 10 for brevity
                    }
    
    # Save trend analysis results
    trend_results = {
        'source_comparison': source_comparison,
        'overlap_analysis': overlap_analysis
    }
    
    with open(os.path.join(output_dir, 'trend_analysis.json'), 'w') as f:
        json.dump(trend_results, f, indent=2, default=str)

def main():
    print("Starting deep analysis of Amazon product data...")
    
    # Load data
    df = load_data()
    if df is None:
        print("No data available for analysis. Exiting.")
        return
    
    print(f"Loaded data with {len(df)} rows and {df.columns.size} columns")
    
    # Price segmentation analysis
    print("Performing price segmentation analysis...")
    df_with_segments = price_segmentation_analysis(df)
    
    # Price elasticity analysis
    print("Analyzing price elasticity...")
    price_elasticity_analysis(df)
    
    # Competitive landscape analysis
    print("Analyzing competitive landscape...")
    competitive_analysis(df)
    
    # Trend analysis
    print("Performing trend analysis...")
    perform_trend_analysis(df)
    
    print(f"Deep analysis complete. Results saved to {output_dir}")

if __name__ == "__main__":
    main() 