# Amazon Product Analysis Project

This project provides a comprehensive analysis of Amazon product data, including bestsellers, trending products, and new releases. The analysis workflow is structured into several modules to facilitate a systematic approach to data cleaning, exploration, deep analysis, and reporting.

## Project Structure

```
amazon_analysis/
├── 1_data_cleaning/              # Data cleaning and preprocessing scripts
├── 2_exploratory_data_analysis/  # EDA scripts and visualizations
├── 3_deep_analysis/              # Advanced analysis and modeling
├── 4_stakeholder_report/         # Report generation for stakeholders
├── cleaned_data/                 # Processed and cleaned datasets
└── README.md                     # This file
```

## Workflow

The analysis workflow follows these sequential steps:

1. **Data Cleaning**: Process raw Amazon product data to remove duplicates, fix inconsistencies, and prepare the data for analysis.

2. **Exploratory Data Analysis (EDA)**: Visualize and analyze the data to understand key patterns, distributions, and relationships between variables.

3. **Deep Analysis**: Perform advanced analysis including price segmentation, price elasticity analysis, and competitive landscape assessment.

4. **Stakeholder Report**: Generate a comprehensive report with actionable insights and strategic recommendations.

## How to Use

### Prerequisites

- Python 3.8+
- Required packages: pandas, numpy, matplotlib, seaborn, scikit-learn, scipy, jinja2, markdown

You can install the required packages using:

```bash
pip install -r requirements.txt
```

### Running the Analysis

1. **Data Cleaning**:
   ```bash
   cd 1_data_cleaning
   python clean_data.py
   ```

2. **Exploratory Data Analysis**:
   ```bash
   cd 2_exploratory_data_analysis
   python exploratory_analysis.py
   ```

3. **Deep Analysis**:
   ```bash
   cd 3_deep_analysis
   python deep_analysis.py
   ```

4. **Generate Report**:
   ```bash
   cd 4_stakeholder_report
   python generate_report.py
   ```

The final report will be generated as an HTML file and automatically opened in your default browser.

## Analysis Components

### Data Cleaning

- Removes duplicate products and session ID entries
- Extracts numerical values from text (prices, ratings, review counts)
- Standardizes product IDs and categories
- Creates clean, consistent datasets for analysis

### Exploratory Data Analysis

- Category distribution analysis
- Price distribution and comparison across categories
- Rating and review analysis
- Prime status impact assessment
- Top product identification

### Deep Analysis

- Price segmentation using K-means clustering
- Price elasticity analysis
- Competitive landscape assessment
- Market concentration measurement
- Cross-category trend analysis

### Stakeholder Report

- Executive summary with key findings
- Methodology documentation
- Detailed market overview
- Strategic insights and recommendations
- Implementation roadmap

## Data Sources

The analysis is based on data scraped from Amazon's:
- Bestsellers lists
- Movers & Shakers (trending products)
- New Releases

## Contributors

This project was developed to provide comprehensive insights into Amazon's product landscape and competitive dynamics.

## License

This project is for educational and research purposes only. 