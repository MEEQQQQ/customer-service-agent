@echo off
echo Fixing CORS issues by redeploying Lambda functions...

echo.
echo Step 1: Install Python dependencies (if needed)
pip install -r requirements.txt

echo.
echo Step 2: Deploy the updated stacks
echo Make sure you have AWS CLI configured and CDK installed
echo.

echo To deploy manually, run these commands:
echo.
echo cdk bootstrap (if not done before)
echo cdk deploy CustomerServiceCore
echo cdk deploy CustomerServiceApi
echo cdk deploy CustomerServiceWeb
echo.

echo The main fixes applied:
echo - Added OPTIONS method handling to all Lambda functions
echo - Updated API Gateway to explicitly handle OPTIONS requests
echo - Added proper CORS headers with Access-Control-Max-Age
echo.

echo After deployment, your CORS issues should be resolved.
echo The API will properly handle preflight OPTIONS requests.

pause