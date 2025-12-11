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
CI-friendly feature testing script.
This script tests core features without requiring external API tokens.
"""

import sys
import os
import subprocess
import tempfile

def test_tool_help(tool_name, tool_path):
    """Test that a tool shows help without errors."""
    try:
        result = subprocess.run([sys.executable, tool_path, "--help"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {tool_name} help works")
            return True
        else:
            print(f"❌ {tool_name} help failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {tool_name} help timed out")
        return False
    except Exception as e:
        print(f"❌ {tool_name} help error: {e}")
        return False

def test_tool_with_env(tool_name, tool_path, env_vars=None):
    """Test that a tool works with environment variables."""
    try:
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        
        result = subprocess.run([sys.executable, tool_path, "--help"], 
                              capture_output=True, text=True, timeout=30, env=env)
        if result.returncode == 0:
            print(f"✅ {tool_name} help works with env vars")
            return True
        else:
            print(f"⚠️  {tool_name} help failed with env vars: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {tool_name} help timed out")
        return False
    except Exception as e:
        print(f"❌ {tool_name} help error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    try:
        # Test basic imports
        import pandas as pd
        import json
        print("✅ Basic imports work")
        
        # Test basic data operations
        data = [{"prompt": "Test", "expected": "false"}]
        df = pd.DataFrame(data)
        assert len(df) == 1
        print("✅ Basic data operations work")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality failed: {e}")
        return False

def main():
    """Run CI-friendly feature tests."""
    print("🧪 Running CI-friendly feature tests...")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test basic functionality
    total_tests += 1
    if test_basic_functionality():
        tests_passed += 1
    
    # Test tools that don't require external APIs
    tools_to_test = [
        ("Dataset Converter", "tools/improved_dataset_converter.py"),
        ("Enhanced Reader", "tools/enhanced_dataset_reader.py"),
        ("Hugging Face Downloader", "download_hf_datasets.py"),
        ("Results Evaluator", "evaluate_existing_results.py"),
        ("Setup Validator", "validate_setup.py")
    ]
    
    for tool_name, tool_path in tools_to_test:
        if os.path.exists(tool_path):
            total_tests += 1
            if test_tool_help(tool_name, tool_path):
                tests_passed += 1
        else:
            print(f"⚠️  {tool_name} not found at {tool_path}")
    
    # Test tools that require environment variables
    env_tools = [
        ("Prompt Evaluator", "prompt_evaluator.py", {"CALYPSOAI_TOKEN": "test_token_12345"}),
        ("Prompt Evaluator Prompts", "prompt_evaluator_prompts.py", {"CALYPSOAI_TOKEN": "test_token_12345"})
    ]
    
    for tool_name, tool_path, env_vars in env_tools:
        if os.path.exists(tool_path):
            total_tests += 1
            if test_tool_with_env(tool_name, tool_path, env_vars):
                tests_passed += 1
        else:
            print(f"⚠️  {tool_name} not found at {tool_path}")
    
    print("=" * 50)
    print(f"Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All CI feature tests passed!")
        return 0
    else:
        print("❌ Some CI feature tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
