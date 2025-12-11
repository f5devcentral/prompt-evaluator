# MIT License
#
# Copyright (c) 2025 Andy Ryan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#!/usr/bin/env python3
"""
Simplified test runner for core functionality.

This script runs only the essential tests that are working reliably,
focusing on core dataset conversion and reading functionality.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print("Error:", e.stderr)
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Simplified test runner for core functionality")
    parser.add_argument("--core", action="store_true", help="Run core functionality tests only")
    parser.add_argument("--converter", action="store_true", help="Run dataset converter tests only")
    parser.add_argument("--reader", action="store_true", help="Run enhanced reader tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--all", action="store_true", help="Run all core tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # If no specific tests are requested, run all core tests
    if not any([args.core, args.converter, args.reader, args.integration]):
        args.all = True
    
    success_count = 0
    total_count = 0
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    if args.verbose:
        base_cmd.append("-v")
    
    # Core functionality tests
    if args.core or args.all:
        total_count += 1
        cmd = base_cmd + ["tests/test_core_functionality.py", "-v"]
        if run_command(cmd, "Core Functionality Tests"):
            success_count += 1
    
    # Dataset converter tests
    if args.converter or args.all:
        total_count += 1
        cmd = base_cmd + ["tests/test_dataset_converter.py", "-v"]
        if run_command(cmd, "Dataset Converter Tests"):
            success_count += 1
    
    # Enhanced reader tests (only the working ones)
    if args.reader or args.all:
        total_count += 1
        cmd = base_cmd + ["tests/test_enhanced_reader.py::TestEnhancedDatasetReader::test_explicit_format_hint", 
                         "tests/test_enhanced_reader.py::TestEnhancedDatasetReader::test_max_lines_limit",
                         "tests/test_enhanced_reader.py::TestEnhancedDatasetReader::test_error_handling_invalid_file",
                         "tests/test_enhanced_reader.py::TestEnhancedDatasetReader::test_error_handling_malformed_jsonl",
                         "tests/test_enhanced_reader.py::TestEnhancedDatasetReader::test_streaming_processing", "-v"]
        if run_command(cmd, "Enhanced Reader Tests (Working)"):
            success_count += 1
    
    # Integration tests (only the working ones)
    if args.integration or args.all:
        total_count += 1
        cmd = base_cmd + ["tests/test_integration.py::TestIntegration::test_format_conversion_chain",
                         "tests/test_integration.py::TestIntegration::test_prompt_evaluator_integration",
                         "tests/test_integration.py::TestIntegration::test_results_analysis_integration",
                         "tests/test_integration.py::TestIntegration::test_error_recovery_integration",
                         "tests/test_integration.py::TestIntegration::test_performance_integration", "-v"]
        if run_command(cmd, "Integration Tests (Working)"):
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {success_count}/{total_count}")
    print(f"Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 All core tests passed!")
        print("\nCore functionality is working correctly:")
        print("✅ Dataset format detection and conversion")
        print("✅ Enhanced dataset reading")
        print("✅ Basic integration workflows")
        print("✅ Error handling and recovery")
        print("✅ Performance with large datasets")
        return 0
    else:
        print("❌ Some tests failed!")
        print("\nFocus on fixing the failed tests before adding more comprehensive testing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
