# Upload Handler Fix

## Issue
Upload handler was failing with error: `{"error": "Upload failed"}`

## Root Causes
1. **Wrong DynamoDB table name**: Default was `'ticket_system'` but actual table is `'ticket_log'`
2. **Missing environment variable**: `TICKET_TABLE` was not set in Lambda configuration
3. **Missing DynamoDB permissions**: upload_handler didn't have permissions to write to DynamoDB

## Fixes Applied

### 1. upload_handler.py
- Changed default table name from `'ticket_system'` to `'ticket_log'`
- Added error details in response for better debugging
- Added `exc_info=True` to logger for full stack traces

### 2. api_stack.py
- Added `TICKET_TABLE` environment variable to upload_handler Lambda
- Granted DynamoDB read/write permissions to upload_handler
- Now both upload_handler and bedrock_handler can access ticket_log table

## Deploy
```bash
cdk deploy CustomerServiceApi
```

## Test
After deployment, the upload endpoint should work correctly and create tickets in DynamoDB.
