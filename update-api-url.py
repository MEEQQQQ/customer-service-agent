#!/usr/bin/env python3
import boto3
import json

def update_lambda_env_vars():
    """Update Lambda environment variables with the deployed API URL"""
    
    # API URL from your deployment
    API_URL = "https://y8i1r0hiv0.execute-api.us-east-1.amazonaws.com/prod"
    
    lambda_client = boto3.client('lambda')
    
    # List of Lambda functions to update
    lambda_functions = [
        'CustomerServiceApi-BedrockHandler433D43D0-*',  # Will need actual function names
        'CustomerServiceApi-UploadHandler4CB020C5-*',
        'CustomerServiceApi-TranscribeHandler8E4C16AC-*',
        'CustomerServiceApi-ImageAnalysisHandlerB09FB8A4-*',
        'CustomerServiceApi-ActionExecutor3835C2EC-*',
        'CustomerServiceApi-AudioProxy15D0FFC9-*'
    ]
    
    # Get actual function names
    response = lambda_client.list_functions()
    actual_functions = []
    
    for func in response['Functions']:
        func_name = func['FunctionName']
        if 'CustomerServiceApi' in func_name:
            actual_functions.append(func_name)
    
    print(f"Found {len(actual_functions)} Lambda functions to update:")
    for func_name in actual_functions:
        print(f"  - {func_name}")
    
    # Update each function
    for func_name in actual_functions:
        try:
            # Get current configuration
            current_config = lambda_client.get_function_configuration(FunctionName=func_name)
            
            # Update environment variables
            env_vars = current_config.get('Environment', {}).get('Variables', {})
            env_vars['API_BASE_URL'] = API_URL
            
            # Update the function
            lambda_client.update_function_configuration(
                FunctionName=func_name,
                Environment={'Variables': env_vars}
            )
            
            print(f"[SUCCESS] Updated {func_name}")
            
        except Exception as e:
            print(f"[ERROR] Failed to update {func_name}: {e}")

if __name__ == "__main__":
    update_lambda_env_vars()
    print("\n[COMPLETE] Lambda environment variables updated successfully!")