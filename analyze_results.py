#!/usr/bin/env python
import json
import os
import sys

def analyze_json_file(filename):
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return
    
    print(f"\n=== Analyzing {filename} ===")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print("File is empty or contains no data")
            return
        
        if isinstance(data, dict):
            print(f"Number of categories: {len(data)}")
            print(f"Categories: {list(data.keys())}")
            
            # Analyze first category
            first_category = next(iter(data.values()))
            if isinstance(first_category, list) and first_category:
                print(f"Number of products in first category: {len(first_category)}")
                
                # Show sample product data
                sample_product = first_category[0]
                print("\nSample product fields:")
                for key, value in sample_product.items():
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"  - {key}: {value}")
        elif isinstance(data, list):
            print(f"Number of items: {len(data)}")
            if data:
                print("\nSample item fields:")
                sample_item = data[0]
                if isinstance(sample_item, dict):
                    for key, value in sample_item.items():
                        # Truncate long values
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        print(f"  - {key}: {value}")
                else:
                    print(f"  {sample_item}")
    
    except json.JSONDecodeError:
        print("Error: File contains invalid JSON")
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")

def main():
    # Get all JSON files in current directory
    json_files = [f for f in os.listdir('.') if f.endswith('.json')]
    
    if not json_files:
        print("No JSON files found in current directory")
        return
    
    print(f"Found {len(json_files)} JSON files")
    
    # Analyze each file
    for filename in json_files:
        analyze_json_file(filename)

if __name__ == "__main__":
    main() 