# CORS Fix for Customer Service Agent

## Problem
You encountered a CORS error when transferring the project to a new AWS account:
```
Access to fetch at 'https://4c1w5gc7e8.execute-api.us-east-1.amazonaws.com/prod/upload' from origin 'https://d332nki4ui0bza.cloudfront.net' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause
The API Gateway was not properly handling CORS preflight OPTIONS requests. When browsers make cross-origin requests, they first send an OPTIONS request to check if the actual request is allowed.

## Fixes Applied

### 1. Lambda Function Updates
Added OPTIONS method handling to all Lambda functions:
- `upload_handler.py`
- `bedrock_handler.py` 
- `transcribe_handler.py`
- `image_analysis_handler.py`
- `action_executor.py`
- `audio_proxy.py`

Each function now includes:
```python
# Handle CORS preflight requests
if event['httpMethod'] == 'OPTIONS':
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Max-Age': '86400'
        },
        'body': ''
    }
```

### 2. API Gateway Updates
Updated `api_stack.py` to explicitly add OPTIONS methods to all endpoints:
- `/upload`
- `/transcribe`
- `/analyze-image`
- `/troubleshoot`
- `/execute-action`
- `/audio/{session_id}`

## Deployment Steps

### Prerequisites
1. Install Python (if not already installed)
2. Install AWS CLI and configure it with your new account credentials
3. Install CDK: `npm install -g aws-cdk`

### Deploy the fixes
```bash
# Navigate to project directory
cd customer-service-agent

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (if not done before in new account)
cdk bootstrap

# Deploy the stacks
cdk deploy CustomerServiceCore
cdk deploy CustomerServiceApi
cdk deploy CustomerServiceWeb
```

## Verification
After deployment:
1. Check that your API Gateway endpoints respond to OPTIONS requests
2. Test the frontend - CORS errors should be resolved
3. Monitor CloudWatch logs for any remaining issues

## Additional Notes
- The `Access-Control-Max-Age: 86400` header caches the preflight response for 24 hours
- All endpoints now allow `*` origins - restrict this in production if needed
- The fixes maintain backward compatibility with existing functionality

## If Issues Persist
1. Check API Gateway console for proper CORS configuration
2. Verify Lambda function logs in CloudWatch
3. Use browser developer tools to inspect network requests
4. Ensure the correct API Gateway URL is being used in the frontend