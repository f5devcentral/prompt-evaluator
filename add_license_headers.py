#!/usr/bin/env python3
"""
Add Apache 2.0 license headers to all Python files in the project.
"""

import os
import glob

LICENSE_HEADER = '''# Copyright 2025 Andy Ryan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''

def has_license_header(content):
    """Check if file already has a license header."""
    stripped = content.strip()
    return stripped.startswith('# Copyright') or stripped.startswith('# Licensed under')

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
