#!/usr/bin/env python3
import boto3
import zipfile
import os
import io

def update_bedrock_handler():
    lambda_client = boto3.client('lambda')
    
    # Create zip file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add the bedrock handler file
        handler_path = 'lambda_functions/bedrock_handler/bedrock_handler.py'
        if os.path.exists(handler_path):
            zip_file.write(handler_path, 'bedrock_handler.py')
            print(f"Added {handler_path} to zip")
        else:
            print(f"ERROR: {handler_path} not found")
            return
    
    zip_buffer.seek(0)
    
    # Update the Lambda function
    function_name = 'customer-service-bedrock-handler'
    
    try:
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_buffer.read()
        )
        print(f"✅ Updated {function_name}")
        print(f"   Last Modified: {response['LastModified']}")
        print(f"   Code Size: {response['CodeSize']} bytes")
        
    except Exception as e:
        print(f"❌ Failed to update {function_name}: {str(e)}")

if __name__ == "__main__":
    update_bedrock_handler()