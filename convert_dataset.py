#!/usr/bin/env python3
"""
Dataset Converter

This script converts CSV datasets to match the format required by the prompt evaluator.
The output format follows the specification in the README:
"prompt text"|expected_result
"""

import csv
import os

def convert_dataset(input_file, output_file):
    """
    Convert the input CSV file to match the format required by the prompt evaluator.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str): Path to the output CSV file
    """
    print(f"Converting {input_file} to {output_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        # Use CSV reader to properly handle quoted fields
        csv_reader = csv.reader(infile)
        
        # Skip the header row if it exists
        try:
            header = next(csv_reader)
            print(f"Found header: {header}")
        except StopIteration:
            print("Warning: Input file is empty")
            return
        
        # Process each row
        for row in csv_reader:
            if len(row) < 2:
                print(f"Warning: Skipping malformed row: {row}")
                continue
                
            prompt, pii = row[0], row[1]
            
            # Convert True/False to true/false (lowercase)
            pii_value = "true" if pii.lower() == "true" else "false"
            
            # Write in the format: "prompt"|true/false
            outfile.write(f'"{prompt}"|{pii_value}\n')
    
    print(f"Conversion complete. Output written to {output_file}")

if __name__ == "__main__":
    print("Dataset Converter")
    print("=================")
    
    # Ask for input file
    while True:
        input_file = input("Enter the path to the input CSV file: ").strip()
        if os.path.exists(input_file):
            break
        else:
            print(f"Error: File '{input_file}' not found. Please try again.")
    
    # Ask for output file
    output_file = input("Enter the name for the output CSV file: ").strip()
    if not output_file:
        output_file = "converted_dataset.csv"
        print(f"Using default output filename: {output_file}")
    
    # Convert the dataset
    convert_dataset(input_file, output_file) 