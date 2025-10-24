#!/usr/bin/env python3
"""
Setup Validation Script

This script validates all prerequisites for running the prompt evaluator application.
It checks for:
- Required environment variables
- Required Python packages
- CalypsoAI API configuration
- Input/output file permissions
- Python version
- Dataset validation
"""

import os
import sys
import pkg_resources
import requests
import csv
import argparse
from dotenv import load_dotenv
from urllib.parse import urljoin

def check_python_version():
    """Check if Python version meets requirements."""
    required_version = (3, 6)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        print("❌ Python version check failed")
        print(f"   Required: Python {required_version[0]}.{required_version[1]}+")
        print(f"   Current: Python {current_version[0]}.{current_version[1]}")
        return False
    
    print("✅ Python version check passed")
    return True

def check_required_packages():
    """Check if all required packages are installed."""
    required_packages = {
        'requests': '2.31.0',
        'pocketflow': '0.0.1',
        'python-dotenv': '1.0.0'
    }
    
    missing_packages = []
    outdated_packages = []
    
    for package, required_version in required_packages.items():
        try:
            installed_version = pkg_resources.get_distribution(package).version
            if pkg_resources.parse_version(installed_version) < pkg_resources.parse_version(required_version):
                outdated_packages.append((package, installed_version, required_version))
        except pkg_resources.DistributionNotFound:
            missing_packages.append(package)
    
    if missing_packages or outdated_packages:
        print("❌ Package check failed")
        if missing_packages:
            print("\nMissing packages:")
            for package in missing_packages:
                print(f"   - {package}")
        if outdated_packages:
            print("\nOutdated packages:")
            for package, current, required in outdated_packages:
                print(f"   - {package}: {current} (required: {required})")
        print("\nTo fix, run:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ Package check passed")
    return True

def check_environment_variables():
    """Check if all required environment variables are set."""
    # Load environment variables from .env file
    load_dotenv()
    load_dotenv(override=True)
    
    required_vars = {
        'CALYPSOAI_URL': 'CalypsoAI API URL',
        'CALYPSOAI_TOKEN': 'CalypsoAI API token'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        if not os.environ.get(var):
            missing_vars.append((var, description))
    
    if missing_vars:
        print("❌ Environment variables check failed")
        print("\nMissing environment variables:")
        for var, description in missing_vars:
            print(f"   - {var} ({description})")
        print("\nTo fix, create or update your .env file with:")
        for var, description in missing_vars:
            print(f"{var}=your_value_here  # {description}")
        return False
    
    print("✅ Environment variables check passed")
    return True


def check_calypsoai_api():
    """Check if CalypsoAI API is accessible."""
    try:
        base_url = urljoin(os.environ.get("CALYPSOAI_URL", "https://www.us1.calypsoai.app"), "/backend/v1")
        api_key = os.environ["CALYPSOAI_TOKEN"]
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        
        # Test API endpoint
        response = requests.get(f"{base_url}/health", headers=headers)
        response.raise_for_status()
        
        print("✅ CalypsoAI API check passed")
        return True
    except Exception as e:
        print("❌ CalypsoAI API check failed")
        print(f"   Error: {str(e)}")
        print("\nTo fix:")
        print("1. Verify your CALYPSOAI_URL is correct")
        print("2. Ensure your CALYPSOAI_TOKEN is valid")
        print("3. Check your internet connection")
        return False

def check_file_permissions():
    """Check if the script has necessary file permissions."""
    try:
        # Check if we can create a test file in the current directory
        test_file = "test_permissions.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        print("✅ File permissions check passed")
        return True
    except Exception as e:
        print("❌ File permissions check failed")
        print(f"   Error: {str(e)}")
        print("\nTo fix:")
        print("1. Ensure you have write permissions in the current directory")
        print("2. Check if the directory is read-only")
        return False

def check_dataset(dataset_path):
    """Check if the dataset exists and is properly formatted."""
    try:
        # Check if file exists
        if not os.path.exists(dataset_path):
            print("❌ Dataset check failed")
            print(f"   File not found: {dataset_path}")
            print("\nTo fix:")
            print("1. Ensure the dataset file exists at the specified path")
            print("2. Check if the path is correct")
            print("3. Make sure you have read permissions for the file")
            return False
        
        # Check if file is readable
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                # Read first line to check format
                first_line = f.readline().strip()
                if '|' not in first_line:
                    print("❌ Dataset check failed")
                    print("   Invalid file format")
                    print("\nTo fix:")
                    print("1. Ensure the file is in CSV format with pipe (|) separator")
                    print("2. Each line should be in the format: \"prompt text\"|expected_result")
                    print("3. Example: \"This is a normal prompt\"|false")
                    return False
                
                # Check if file is empty
                if not first_line:
                    print("❌ Dataset check failed")
                    print("   File is empty")
                    print("\nTo fix:")
                    print("1. Ensure the dataset file contains data")
                    return False
                
                # Validate all lines
                f.seek(0)  # Reset file pointer to beginning
                reader = csv.reader(f, delimiter='|')
                line_count = 0
                valid_lines = 0
                
                for line in reader:
                    line_count += 1
                    if len(line) == 2 and line[1].lower() in ['true', 'false']:
                        valid_lines += 1
                    else:
                        print(f"❌ Dataset check failed")
                        print(f"   Invalid format at line {line_count}")
                        print(f"   Expected format: \"prompt text\"|true/false")
                        print(f"   Found: {'|'.join(line)}")
                        print("\nTo fix:")
                        print("1. Ensure each line follows the format: \"prompt text\"|expected_result")
                        print("2. expected_result should be either 'true' or 'false'")
                        return False
                
                if valid_lines == 0:
                    print("❌ Dataset check failed")
                    print("   No valid lines found in the dataset")
                    print("\nTo fix:")
                    print("1. Ensure the dataset contains at least one valid line")
                    print("2. Each line should be in the format: \"prompt text\"|expected_result")
                    return False
                
                print(f"✅ Dataset check passed")
                print(f"   Found {valid_lines} valid lines in {dataset_path}")
                return True
                
        except UnicodeDecodeError:
            print("❌ Dataset check failed")
            print("   File encoding error")
            print("\nTo fix:")
            print("1. Ensure the file is saved with UTF-8 encoding")
            return False
            
    except Exception as e:
        print("❌ Dataset check failed")
        print(f"   Error: {str(e)}")
        print("\nTo fix:")
        print("1. Check if the file path is correct")
        print("2. Ensure you have read permissions for the file")
        print("3. Verify the file is not corrupted")
        return False

def main():
    """Run all validation checks."""
    parser = argparse.ArgumentParser(description='Validate setup for Prompt Evaluator')
    parser.add_argument('--dataset', '-d', type=str, required=True,
                      help='Path to the input dataset file')
    args = parser.parse_args()
    
    print("\n=== Prompt Evaluator Setup Validation ===\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("Environment Variables", check_environment_variables),
        ("CalypsoAI API", check_calypsoai_api),
        ("File Permissions", check_file_permissions),
        ("Dataset", lambda: check_dataset(args.dataset))
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        if not check_func():
            all_passed = False
    
    print("\n=== Validation Summary ===")
    if all_passed:
        print("\n✅ All checks passed! The application is ready to run.")
    else:
        print("\n❌ Some checks failed. Please fix the issues above before running the application.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 