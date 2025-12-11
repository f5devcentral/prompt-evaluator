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
Simple test script to verify GitLab CI environment.
This script tests basic functionality without complex dependencies.
"""

import sys
import os
import tempfile
import json

def test_basic_imports():
    """Test that basic modules can be imported."""
    try:
        import pandas as pd
        import json
        print("✅ Basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_file_structure():
    """Test that required files exist."""
    required_files = [
        'tests/test_core_functionality.py',
        'tests/test_dataset_converter.py',
        'tests/test_enhanced_reader.py',
        'tests/test_integration.py',
        'tests/test_runner_simple.py',
        'requirements.txt',
        'requirements-test.txt',
        'pytest.ini'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_basic_functionality():
    """Test basic functionality without complex dependencies."""
    try:
        # Test basic data structures
        data = [{"prompt": "Test", "expected": "false"}]
        json_str = json.dumps(data[0])
        parsed = json.loads(json_str)
        
        if parsed["prompt"] == "Test":
            print("✅ Basic functionality working")
            return True
        else:
            print("❌ Basic functionality failed")
            return False
    except Exception as e:
        print(f"❌ Basic functionality error: {e}")
        return False

def test_temp_file_creation():
    """Test that temporary files can be created."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            print("✅ Temporary file creation working")
            return True
        else:
            print("❌ Temporary file creation failed")
            return False
    except Exception as e:
        print(f"❌ Temporary file creation error: {e}")
        return False

def main():
    """Run all basic tests."""
    print("🧪 Running GitLab CI environment tests...")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_file_structure,
        test_basic_functionality,
        test_temp_file_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
