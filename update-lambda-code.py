#!/usr/bin/env python3
import boto3
import zipfile
import os
import io

def update_lambda_function(function_name, code_path):
    """Update a Lambda function with new code"""
    lambda_client = boto3.client('lambda')
    
    # Create a zip file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(code_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, code_path)
                    zip_file.write(file_path, arcname)
    
    zip_buffer.seek(0)
    
    try:
        # Update the function code
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_buffer.read()
        )
        print(f"[SUCCESS] Updated {function_name}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update {function_name}: {e}")
        return False

def main():
    """Update all Lambda functions"""
    lambda_client = boto3.client('lambda')
    
    # Get list of functions
    response = lambda_client.list_functions()
    functions = response['Functions']
    
    # Find our functions
    function_mappings = {}
    for func in functions:
        func_name = func['FunctionName']
        if 'CustomerServiceApi' in func_name:
            if 'TranscribeHandler' in func_name:
                function_mappings[func_name] = 'lambda_functions/transcribe_handler'
            elif 'ImageAnalysisHandler' in func_name:
                function_mappings[func_name] = 'lambda_functions/image_analysis_handler'
            elif 'UploadHandler' in func_name:
                function_mappings[func_name] = 'lambda_functions/upload_handler'
            elif 'BedrockHandler' in func_name:
                function_mappings[func_name] = 'lambda_functions/bedrock_handler'
            elif 'ActionExecutor' in func_name:
                function_mappings[func_name] = 'lambda_functions/action_executor'
            elif 'AudioProxy' in func_name:
                function_mappings[func_name] = 'lambda_functions/audio_proxy'
    
    print(f"Found {len(function_mappings)} functions to update:")
    for func_name, code_path in function_mappings.items():
        print(f"  - {func_name} -> {code_path}")
    
    # Update each function
    success_count = 0
    for func_name, code_path in function_mappings.items():
        if update_lambda_function(func_name, code_path):
            success_count += 1
    
    print(f"\n[COMPLETE] Successfully updated {success_count}/{len(function_mappings)} Lambda functions!")

if __name__ == "__main__":
    main()