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
            
            # Replace newlines with spaces and strip extra whitespace
            prompt = ' '.join(prompt.split())
            
            # Convert True/False to true/false (lowercase)
            pii_value = "true" if pii.lower() == "true" else "false"
            
            # Write in the format: """prompt"""|true/false
            outfile.write(f'"""{prompt}"""|{pii_value}\n')
    
    print(f"Conversion complete. Output written to {output_file}")

if __name__ == "__main__":
    print("Dataset Converter")
    print("=================")
    
    # Define the datasets directory
    datasets_dir = "datasets"
    
    # Check if the datasets directory exists
    if not os.path.exists(datasets_dir):
        print(f"Note: '{datasets_dir}' directory not found. It will be created if you save a file there.")
    
    # Ask for input file
    while True:
        input_file = input("Enter the path to the input CSV file: ").strip()
        
        # If the input file is in the datasets directory, suggest the full path
        if not os.path.dirname(input_file) and os.path.exists(os.path.join(datasets_dir, input_file)):
            input_file = os.path.join(datasets_dir, input_file)
            print(f"Using file from datasets directory: {input_file}")
        
        if os.path.exists(input_file):
            break
        else:
            print(f"Error: File '{input_file}' not found. Please try again.")
    
    # Ask for output file
    output_file = input("Enter the name for the output CSV file: ").strip()
    if not output_file:
        output_file = "converted_dataset.csv"
        print(f"Using default output filename: {output_file}")
    
    # If the output file doesn't have a directory specified, suggest saving to datasets
    if not os.path.dirname(output_file):
        datasets_output = os.path.join(datasets_dir, output_file)
        save_to_datasets = input(f"Save output to '{datasets_output}'? (y/n): ").strip().lower()
        if save_to_datasets == 'y':
            output_file = datasets_output
            # Create the datasets directory if it doesn't exist
            os.makedirs(datasets_dir, exist_ok=True)
    
    # Convert the dataset
    convert_dataset(input_file, output_file) 