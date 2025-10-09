#!/usr/bin/env python3
"""
Script to update CORS headers in all Lambda functions to allow both CloudFront and localhost
"""

import os
import re

def update_cors_headers(file_path):
    """Update CORS headers in a Lambda function file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the new CORS origin header that allows both CloudFront and localhost
    new_origin = "'https://d332nki4ui0bza.cloudfront.net' if 'cloudfront' in event.get('headers', {}).get('origin', '') else 'http://localhost:3000'"
    
    # Pattern to match Access-Control-Allow-Origin lines
    patterns = [
        (r"'Access-Control-Allow-Origin': '\*'", f"'Access-Control-Allow-Origin': {new_origin}"),
        (r"'Access-Control-Allow-Origin': 'https://d332nki4ui0bza\.cloudfront\.net'", f"'Access-Control-Allow-Origin': {new_origin}"),
        (r'"Access-Control-Allow-Origin": "\*"', f'"Access-Control-Allow-Origin": {new_origin}'),
        (r'"Access-Control-Allow-Origin": "https://d332nki4ui0bza\.cloudfront\.net"', f'"Access-Control-Allow-Origin": {new_origin}')
    ]
    
    updated = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            updated = True
    
    if updated:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")
    else:
        print(f"No changes needed: {file_path}")

def main():
    lambda_functions_dir = "lambda_functions"
    
    # Find all Python files in lambda_functions directory
    for root, dirs, files in os.walk(lambda_functions_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                update_cors_headers(file_path)

if __name__ == "__main__":
    main()