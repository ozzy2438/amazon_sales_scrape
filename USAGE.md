# Amazon Product Analysis Pipeline - Usage Guide

This document provides detailed instructions on how to use the Amazon product analysis pipeline to generate insights from Amazon product data.

## Prerequisites

Before using the pipeline, ensure you have:

1. **Python Environment**: Python 3.8 or higher installed
2. **Required Packages**: Install all dependencies using:
   ```bash
   pip install -r requirements.txt
   ```
3. **Source Data**: Amazon product data files in JSON format:
   - `amazon_bestsellers.json`: Data from Amazon's bestseller lists
   - `amazon_trends.json`: Data from Amazon's "Movers & Shakers" section
   - `amazon_new_releases.json`: Data from Amazon's new releases section

## Running the Complete Pipeline

The simplest way to run the entire analysis is to use the `run_all.py` script:

```bash
cd amazon_analysis
python run_all.py
```

This will:
1. Clean the data
2. Run exploratory data analysis
3. Perform deep analysis
4. Generate the stakeholder report
5. Open the report in your default browser

The complete process typically takes 5-10 minutes depending on your hardware.

## Running Individual Components

You can also run each component of the pipeline separately:

### 1. Data Cleaning

```bash
cd amazon_analysis/1_data_cleaning
python clean_data.py
```

This component:
- Processes raw JSON data files
- Removes duplicates and anomalies
- Extracts numerical values from text
- Creates standardized datasets
- Outputs cleaned CSV and Parquet files to the `amazon_analysis/cleaned_data/` directory

### 2. Exploratory Data Analysis

```bash
cd amazon_analysis/2_exploratory_data_analysis
python exploratory_analysis.py
```

This component:
- Analyzes price, rating, and review distributions
- Creates visualizations for key metrics
- Performs category-level comparisons
- Outputs visualizations to the `amazon_analysis/2_exploratory_data_analysis/visualizations/` directory

### 3. Deep Analysis

```bash
cd amazon_analysis/3_deep_analysis
python deep_analysis.py
```

This component:
- Performs price segmentation using clustering
- Analyzes price elasticity
- Assesses competitive landscape
- Examines cross-category trends
- Outputs results to the `amazon_analysis/3_deep_analysis/results/` directory

### 4. Stakeholder Report Generation

```bash
cd amazon_analysis/4_stakeholder_report
python generate_report.py
```

This component:
- Compiles insights from all previous analyses
- Generates an HTML report with visualizations
- Creates executive summary and recommendations
- Outputs the report to `amazon_analysis/4_stakeholder_report/report/` directory

## Interpreting the Results

The final report provides comprehensive insights into Amazon's product landscape:

1. **Executive Summary**: Key findings and high-level insights
2. **Market Overview**: Category distribution, pricing landscape, and customer satisfaction metrics
3. **Deep Insights**: Price segmentation, price-quality relationships, and competitive dynamics
4. **Strategic Recommendations**: Actionable strategies for pricing, product development, and marketing

## Customizing the Analysis

To customize the analysis:

1. **Modify Parameters**: Each component has configurable parameters at the top of its script file
2. **Add New Visualizations**: Add new visualization code to the appropriate analysis scripts
3. **Extend the Report**: Modify the report template in `generate_report.py`

## Troubleshooting

Common issues and solutions:

1. **Missing Data Files**: Ensure all required JSON files are in the project root directory
2. **Memory Errors**: For large datasets, increase available memory or modify the scripts to process data in chunks
3. **Visualization Errors**: Ensure matplotlib and seaborn are correctly installed
4. **Report Generation Issues**: Check that all previous analysis steps completed successfully

## Support and Feedback

For support or to provide feedback on the analysis pipeline, please open an issue on the GitHub repository or contact the maintainer directly. 