"""
Boolean Syntax Fixer for JavaScript-to-Python Style Conversion

This script scans Python files in the project and fixes JavaScript-style boolean values
(True, False) to Python-style (True, False).
"""
import os
import re
import sys

def fix_boolean_syntax(file_path):
    """
    Fix JavaScript-style booleans in Python files
    
    Args:
        file_path: Path to the Python file to fix
        
    Returns:
        bool: True if changes were made, False otherwise
    """
    print(f"Checking file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for JavaScript-style booleans outside of strings/comments
        original_content = content
        
        # Fix 'true' to 'True'
        pattern_True = re.compile(r'(?<![\'"])True(?![\'"])')
        content = pattern_True.sub('True', content)
        
        # Fix 'false' to 'False'
        pattern_False = re.compile(r'(?<![\'"])False(?![\'"])')
        content = pattern_False.sub('False', content)
        
        # Check if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Fixed JavaScript-style booleans in {file_path}")
            return True
        else:
            print(f"  No issues found in {file_path}")
            return False
    
    except Exception as e:
        print(f"  Error processing {file_path}: {str(e)}")
        return False

def scan_directory(directory):
    """
    Scan a directory recursively for Python files and fix boolean syntax
    
    Args:
        directory: Root directory to scan
        
    Returns:
        int: Number of files fixed
    """
    files_fixed = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_boolean_syntax(file_path):
                    files_fixed += 1
    
    return files_fixed

if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Scanning directory: {project_dir}")
    files_fixed = scan_directory(project_dir)
    
    print(f"\nFixed JavaScript-style booleans in {files_fixed} files.")
    print("Now your quantum trading system should be free of JavaScript-style syntax errors!")
