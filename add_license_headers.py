#!/usr/bin/env python3
"""
Add MIT license headers to all Python files in the project.
"""

import os
import glob

LICENSE_HEADER = '''# MIT License
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
'''

def has_license_header(content):
    """Check if file already has a license header."""
    return content.strip().startswith('# MIT License')

def add_license_header(file_path):
    """Add license header to a Python file if it doesn't already have one."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if header already exists
    if has_license_header(content):
        print(f"Skipping {file_path} (already has header)")
        return False
    
    # Add header with blank line after it
    new_content = LICENSE_HEADER + '\n' + content
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Added header to {file_path}")
    return True

def main():
    """Add license headers to all Python files."""
    # Find all Python files
    python_files = []
    
    # Root level Python files
    python_files.extend(glob.glob('*.py'))
    
    # Subdirectory Python files
    python_files.extend(glob.glob('tests/*.py'))
    python_files.extend(glob.glob('tools/*.py'))
    
    # Filter out the add_license_headers.py script itself
    python_files = [f for f in python_files if f != 'add_license_headers.py']
    
    if not python_files:
        print("No Python files found!")
        return
    
    print(f"Found {len(python_files)} Python files to process\n")
    
    modified_count = 0
    for file_path in sorted(python_files):
        if os.path.isfile(file_path):
            if add_license_header(file_path):
                modified_count += 1
    
    print(f"\nModified {modified_count} files")

if __name__ == '__main__':
    main()
