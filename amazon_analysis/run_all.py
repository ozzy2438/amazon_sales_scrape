#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from datetime import datetime

def print_step(step_number, step_name):
    """Print a formatted step header"""
    print("\n" + "="*80)
    print(f"STEP {step_number}: {step_name}")
    print("="*80 + "\n")

def run_script(script_path, description):
    """Run a Python script and handle errors"""
    try:
        start_time = time.time()
        print(f"Starting: {description}...")
        
        # Get the directory of the script
        script_dir = os.path.dirname(os.path.abspath(script_path))
        
        # Run the script
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=script_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Print output
        print(result.stdout)
        
        # Check for errors
        if result.stderr:
            print(f"Warnings/Errors: {result.stderr}")
        
        elapsed_time = time.time() - start_time
        print(f"Completed: {description} in {elapsed_time:.2f} seconds\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print(f"Exit code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Run the complete analysis workflow"""
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Record start time
    start_time = time.time()
    print(f"Starting Amazon Product Analysis Workflow at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Data Cleaning
    print_step(1, "Data Cleaning")
    data_cleaning_script = os.path.join(base_dir, "1_data_cleaning", "clean_data.py")
    if not run_script(data_cleaning_script, "Data Cleaning"):
        print("Data cleaning failed. Exiting.")
        return
    
    # Step 2: Exploratory Data Analysis
    print_step(2, "Exploratory Data Analysis")
    eda_script = os.path.join(base_dir, "2_exploratory_data_analysis", "exploratory_analysis.py")
    if not run_script(eda_script, "Exploratory Data Analysis"):
        print("Exploratory Data Analysis failed. Continuing with partial results...")
    
    # Step 3: Deep Analysis
    print_step(3, "Deep Analysis")
    deep_analysis_script = os.path.join(base_dir, "3_deep_analysis", "deep_analysis.py")
    if not run_script(deep_analysis_script, "Deep Analysis"):
        print("Deep Analysis failed. Continuing with partial results...")
    
    # Step 4: Generate Stakeholder Report
    print_step(4, "Stakeholder Report Generation")
    report_script = os.path.join(base_dir, "4_stakeholder_report", "generate_report.py")
    if not run_script(report_script, "Report Generation"):
        print("Report generation failed.")
    
    # Calculate total execution time
    total_time = time.time() - start_time
    print(f"\nComplete analysis workflow finished in {total_time/60:.2f} minutes")
    print(f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print report location
    report_path = os.path.join(base_dir, "4_stakeholder_report", "report", "amazon_product_analysis_report.html")
    if os.path.exists(report_path):
        print(f"\nFinal report is available at: {report_path}")
    else:
        print("\nFinal report was not generated successfully.")

if __name__ == "__main__":
    main() 