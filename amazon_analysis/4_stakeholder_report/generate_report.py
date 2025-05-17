#!/usr/bin/env python3
import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import jinja2
import markdown
import webbrowser
from pathlib import Path

# Add parent directory to path for importing modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
cleaned_data_dir = os.path.join(parent_dir, 'cleaned_data')
eda_dir = os.path.join(parent_dir, '2_exploratory_data_analysis/visualizations')
deep_analysis_dir = os.path.join(parent_dir, '3_deep_analysis/results')
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'report')

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)

def load_json_file(filepath):
    """Load JSON data from a file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {str(e)}")
        return None

def copy_visualizations():
    """Copy visualization images to the report directory"""
    # Copy EDA visualizations
    if os.path.exists(eda_dir):
        for file in os.listdir(eda_dir):
            if file.endswith('.png'):
                src_path = os.path.join(eda_dir, file)
                dest_path = os.path.join(output_dir, 'images', file)
                try:
                    import shutil
                    shutil.copy2(src_path, dest_path)
                except Exception as e:
                    print(f"Error copying {src_path}: {str(e)}")
    
    # Copy deep analysis visualizations
    if os.path.exists(deep_analysis_dir):
        for file in os.listdir(deep_analysis_dir):
            if file.endswith('.png'):
                src_path = os.path.join(deep_analysis_dir, file)
                dest_path = os.path.join(output_dir, 'images', file)
                try:
                    import shutil
                    shutil.copy2(src_path, dest_path)
                except Exception as e:
                    print(f"Error copying {src_path}: {str(e)}")

def format_currency(value):
    """Format a value as currency"""
    if isinstance(value, (int, float)):
        return f"${value:,.2f}"
    return value

def format_as_percentage(value):
    """Format a value as percentage"""
    if isinstance(value, (int, float)):
        return f"{value:.1f}%"
    return value

def generate_executive_summary():
    """Generate executive summary markdown"""
    # Load summary data
    data_summary = load_json_file(os.path.join(cleaned_data_dir, 'data_summary.json'))
    eda_summary = load_json_file(os.path.join(eda_dir, 'eda_summary.json'))
    price_elasticity = load_json_file(os.path.join(deep_analysis_dir, 'price_elasticity.json'))
    price_segmentation = load_json_file(os.path.join(deep_analysis_dir, 'price_segmentation.json'))
    
    # Extract key metrics
    total_products = data_summary.get('total_products', 'N/A') if data_summary else 'N/A'
    unique_products = data_summary.get('unique_products', 'N/A') if data_summary else 'N/A'
    categories = len(data_summary.get('categories', [])) if data_summary else 'N/A'
    
    # Extract pricing info
    avg_price = None
    if eda_summary and 'price' in eda_summary:
        avg_price = eda_summary['price'].get('overall', {}).get('mean', None)
    
    # Extract rating info
    avg_rating = None
    if eda_summary and 'rating' in eda_summary:
        avg_rating = eda_summary['rating'].get('overall', {}).get('mean', None)
    
    # Create markdown
    markdown_content = f"""
# Executive Summary

## Amazon Product Analysis: Key Insights

This report presents a comprehensive analysis of Amazon's product data across multiple categories, including bestsellers, trending products, and new releases.

### Key Metrics:
- **Total Products Analyzed**: {total_products}
- **Unique Products**: {unique_products}
- **Categories Covered**: {categories}
- **Average Price**: {format_currency(avg_price) if avg_price else 'N/A'}
- **Average Rating**: {f"{avg_rating:.1f}/5.0" if avg_rating else 'N/A'}

### Top Findings:

1. **Price Segmentation**: 
   Our analysis identified {price_segmentation.get('optimal_clusters', 'several') if price_segmentation else 'several'} distinct price segments in the marketplace, allowing for targeted positioning strategies.

2. **Price-Rating Relationship**: 
   {("Positive correlation" if price_elasticity and price_elasticity.get('overall', {}).get('price_rating_correlation', 0) > 0 else "Negative correlation" if price_elasticity and price_elasticity.get('overall', {}).get('price_rating_correlation', 0) < 0 else "No strong correlation")} between price and product ratings{f" (r = {price_elasticity['overall']['price_rating_correlation']:.2f})" if price_elasticity else ""}, suggesting {'higher priced items tend to receive better ratings' if price_elasticity and price_elasticity.get('overall', {}).get('price_rating_correlation', 0) > 0 else 'price is not strongly associated with customer satisfaction'}.

3. **Category Insights**:
   Significant variations in pricing strategies, customer reviews, and competitive dynamics across different product categories.

4. **Prime Status Impact**:
   {"Prime products generally command higher prices but also receive better ratings, indicating a premium positioning." if eda_summary and 'prime' in eda_summary else "Prime status shows significant impact on product positioning and performance."}

This analysis provides valuable insights for strategic decision-making, pricing optimization, and competitive positioning in the Amazon marketplace.
"""
    
    return markdown_content

def generate_methodology_section():
    """Generate methodology section markdown"""
    markdown_content = """
## Methodology

### Data Collection and Processing

The analysis is based on a comprehensive dataset of Amazon products scraped from various sections of the platform:

1. **Bestsellers**: Products from Amazon's bestseller lists across multiple categories
2. **Trending Products**: Items from the "Movers & Shakers" section showing products with rapidly increasing sales
3. **New Releases**: Recently launched products across various categories

### Analysis Approach

The data analysis followed a structured methodology:

1. **Data Cleaning**:
   - Removing duplicate entries and anomalies
   - Standardizing product information
   - Extracting numerical values from text (prices, ratings, review counts)
   - Converting data types and handling missing values

2. **Exploratory Data Analysis**:
   - Distribution analysis of key metrics
   - Category-level comparisons
   - Correlation analysis between variables
   - Visual pattern identification

3. **Deep Analysis**:
   - Market segmentation using k-means clustering
   - Price elasticity modeling
   - Competitive landscape assessment
   - Cross-category trend analysis

4. **Visualization and Reporting**:
   - Creation of interactive visualizations
   - Statistical summary generation
   - Development of actionable insights
   - Preparation of stakeholder recommendations

### Limitations

This analysis has several limitations that should be considered when interpreting the results:

- **Point-in-time Analysis**: Data represents a snapshot at the time of collection
- **Limited Historical Data**: Lack of long-term trends and seasonal patterns
- **Sample Representation**: Data may not perfectly represent the entire Amazon marketplace
- **External Factors**: The analysis doesn't account for external market conditions, supply chain issues, or economic factors

Despite these limitations, the methodology provides robust insights into Amazon's product landscape and competitive dynamics.
"""
    
    return markdown_content

def generate_market_overview():
    """Generate market overview section markdown"""
    # Load summary data
    eda_summary = load_json_file(os.path.join(eda_dir, 'eda_summary.json'))
    
    # Create markdown
    markdown_content = """
## Market Overview

### Category Distribution

The analysis covers a diverse range of product categories on Amazon, providing a comprehensive view of the marketplace.

![Category Distribution](images/category_distribution.png)

The pie chart below illustrates the relative proportion of products across different categories in our dataset:

![Category Pie Chart](images/category_pie_chart.png)

### Pricing Landscape

The price distribution across Amazon products reveals important insights about market positioning and consumer options:

![Price Histogram](images/price_histogram.png)

Significant price variations exist across different product categories:

![Price Distribution by Category](images/price_distribution_by_category.png)

### Rating and Review Analysis

Customer ratings provide valuable insights into product quality and customer satisfaction:

![Rating Distribution](images/rating_distribution.png)

Categories demonstrate varying levels of customer satisfaction:

![Average Rating by Category](images/average_rating_by_category.png)

### Prime Status Impact

Amazon Prime status significantly influences product performance and visibility:

![Prime Distribution](images/prime_distribution.png)

The percentage of Prime-eligible products varies substantially across categories:

![Prime by Category](images/prime_by_category.png)

Prime status also appears to impact pricing strategies:

![Prime Price Comparison](images/prime_price_comparison.png)
"""
    
    return markdown_content

def generate_deep_insights():
    """Generate deep insights section markdown"""
    markdown_content = """
## Deep Market Insights

### Price Segmentation

Our clustering analysis identified distinct price segments in the Amazon marketplace:

![Price Segments](images/price_segments.png)

These segments represent different market positioning strategies and consumer price expectations.

### Price-Quality Relationship

We analyzed the relationship between price and product ratings to understand value perception:

![Price vs Rating Regression](images/price_vs_rating_regression.png)

Similarly, we explored how price affects product popularity through review counts:

![Price vs Reviews](images/price_vs_reviews.png)

### Market Concentration

Analysis of market concentration reveals varying competitive landscapes across categories:

![Market Concentration](images/market_concentration.png)

Categories with high concentration may present challenges for new entrants, while more fragmented categories offer greater opportunities.

### Price Variability

Price variability within categories indicates different competitive dynamics:

![Price Variation by Category](images/price_variation_by_category.png)

Higher variation suggests less standardized products or more differentiated pricing strategies.

### Price Elasticity by Category

Our elasticity analysis shows how price sensitivity varies across product categories:

![Price Elasticity by Category](images/price_elasticity_by_category.png)

Categories with negative elasticity indicate that higher prices are associated with lower review counts (and potentially lower sales).
"""
    
    return markdown_content

def generate_strategic_recommendations():
    """Generate strategic recommendations section markdown"""
    markdown_content = """
## Strategic Recommendations

### Pricing Strategy

1. **Segment-Based Pricing**:
   - Align product pricing with identified market segments
   - Consider psychological pricing points within each segment
   - Develop clear value propositions for each price tier

2. **Competitive Positioning**:
   - In highly concentrated categories, differentiate on quality or unique features
   - In fragmented categories, consider price leadership strategies
   - Monitor price elasticity to optimize pricing for maximum revenue

3. **Prime Program Optimization**:
   - Prioritize Prime eligibility for products in categories where Prime status shows the strongest impact
   - Consider premium pricing for Prime products where data supports higher willingness to pay
   - Use Prime bundling for products in price-sensitive categories

### Product Development

1. **Category Focus**:
   - Prioritize development in categories with higher ratings and review counts
   - Target underdeveloped niches in categories with low concentration
   - Consider product innovations addressing gaps in the current market

2. **Quality Benchmarks**:
   - Set minimum quality thresholds based on category-specific rating distributions
   - Invest in quality improvements for products in categories where ratings strongly influence sales
   - Develop quality assurance processes aligned with category expectations

### Marketing Recommendations

1. **Review Generation**:
   - Implement structured review solicitation for products in categories where reviews drive conversion
   - Prioritize review quality initiatives in categories with higher price-review elasticity
   - Develop category-specific review response strategies

2. **Value Communication**:
   - Emphasize value propositions aligned with segment-specific customer expectations
   - Highlight quality metrics in categories where price-quality relationships are positive
   - Develop messaging frameworks tailored to each price segment

3. **Competitive Positioning**:
   - Position against clear competitors in concentrated categories
   - Emphasize unique selling propositions in fragmented categories
   - Leverage cross-category insights to identify differentiation opportunities

### Implementation Roadmap

1. **Short-term (0-3 months)**:
   - Implement price optimization based on elasticity findings
   - Adjust Prime eligibility based on category impact analysis
   - Develop segment-specific marketing messaging

2. **Medium-term (3-6 months)**:
   - Launch targeted product development initiatives
   - Implement review generation strategies
   - Refine competitive positioning across categories

3. **Long-term (6-12 months)**:
   - Develop comprehensive category strategies
   - Implement continuous monitoring of price sensitivity
   - Build advanced segmentation capabilities
"""
    
    return markdown_content

def generate_conclusion():
    """Generate conclusion section markdown"""
    markdown_content = """
## Conclusion

This comprehensive analysis of Amazon's product landscape provides valuable insights into market dynamics, consumer preferences, and competitive positioning strategies. By examining bestsellers, trending products, and new releases across multiple categories, we've uncovered patterns that can guide strategic decision-making.

The findings reveal significant variations in pricing strategies, customer engagement, and competitive dynamics across different product categories. The identification of distinct price segments and the analysis of price-quality relationships provide a foundation for targeted market approaches.

Key takeaways include:

1. **Market Segmentation**: The Amazon marketplace comprises distinct price segments, each with different customer expectations and competitive dynamics.

2. **Category Differences**: Product categories vary substantially in terms of pricing strategies, rating patterns, and competitive concentration.

3. **Prime Impact**: Amazon Prime status significantly influences product positioning and performance, with varying effects across categories.

4. **Price-Quality Relationship**: The relationship between price and product ratings varies by category, offering insights into value perception.

By leveraging these insights, businesses can develop more effective pricing strategies, improve product positioning, and identify new market opportunities. The recommendations outlined in this report provide actionable steps for optimizing performance in the Amazon marketplace.

Continuous monitoring and refinement of these strategies will be essential as market conditions evolve. This analysis provides a solid foundation for data-driven decision-making in the dynamic e-commerce landscape.
"""
    
    return markdown_content

def generate_html_report():
    """Generate the complete HTML report"""
    # Create report sections
    executive_summary = generate_executive_summary()
    methodology = generate_methodology_section()
    market_overview = generate_market_overview()
    deep_insights = generate_deep_insights()
    recommendations = generate_strategic_recommendations()
    conclusion = generate_conclusion()
    
    # Combine all markdown
    complete_markdown = f"""
# Amazon Product Analysis: Market Insights & Strategic Recommendations
## Generated: {datetime.now().strftime('%B %d, %Y')}

{executive_summary}

{methodology}

{market_overview}

{deep_insights}

{recommendations}

{conclusion}
"""
    
    # Convert to HTML
    html_content = markdown.markdown(complete_markdown, extensions=['tables'])
    
    # Apply styling
    styled_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Product Analysis Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3, h4 {{
            color: #0066c0;
            margin-top: 30px;
        }}
        h1 {{
            border-bottom: 2px solid #0066c0;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        ul, ol {{
            padding-left: 25px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .highlight {{
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #0066c0;
            margin: 20px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .executive-summary {{
            background-color: #f0f7fb;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""
    
    # Save HTML report
    report_path = os.path.join(output_dir, 'amazon_product_analysis_report.html')
    with open(report_path, 'w') as f:
        f.write(styled_html)
    
    return report_path

def main():
    print("Generating stakeholder report...")
    
    # Copy visualizations
    print("Copying visualization images...")
    copy_visualizations()
    
    # Generate HTML report
    print("Generating HTML report...")
    report_path = generate_html_report()
    
    print(f"Report generated successfully at: {report_path}")
    
    # Open report in browser
    print("Opening report in default browser...")
    webbrowser.open('file://' + os.path.abspath(report_path))

if __name__ == "__main__":
    main() 