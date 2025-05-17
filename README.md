# Amazon Huge Sales Data Analysis

This repository contains a comprehensive analysis of Amazon product data, including bestsellers, trending products, and new releases. The analysis provides valuable insights into market dynamics, competitive positioning, and strategic opportunities.

## Project Structure

The project is organized into two main components:

1. **Data Collection** (`main.py`): Scrapes product data from Amazon using advanced web crawling techniques.
2. **Data Analysis** (`amazon_analysis/`): Processes and analyzes the collected data to generate actionable insights.

## Getting Started

### Prerequisites

- Python 3.8+
- Required packages for data collection and analysis (see `requirements.txt` and `amazon_analysis/requirements.txt`)

### Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r amazon_analysis/requirements.txt
   ```

### Running the Analysis

You can run the analysis pipeline in two ways:

1. **Complete workflow** (from data collection to report generation):
   ```bash
   # First, collect data from Amazon
   python main.py
   
   # Then, run the analysis pipeline
   cd amazon_analysis
   python run_all.py
   ```

2. **Analysis only** (if you already have the data):
   ```bash
   cd amazon_analysis
   python run_all.py
   ```

## Analysis Components

The analysis consists of four main components:

1. **Data Cleaning**: Processes raw data to remove duplicates, fix inconsistencies, and prepare for analysis.
2. **Exploratory Data Analysis**: Visualizes key patterns, distributions, and relationships.
3. **Deep Analysis**: Performs advanced analysis including price segmentation, elasticity analysis, and competitive landscape assessment.
4. **Stakeholder Report**: Generates a comprehensive report with actionable insights and recommendations.

## Results

After running the analysis, you'll find:

- Cleaned datasets in `amazon_analysis/cleaned_data/`
- Visualizations in `amazon_analysis/2_exploratory_data_analysis/visualizations/`
- Advanced analysis results in `amazon_analysis/3_deep_analysis/results/`
- A comprehensive stakeholder report in `amazon_analysis/4_stakeholder_report/report/`

## License

This project is for educational and research purposes only. 