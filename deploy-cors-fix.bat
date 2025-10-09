@echo off
echo Deploying CORS fixes...

echo Installing dependencies...
pip install -r requirements.txt

echo Deploying CDK stacks...
cdk deploy CustomerServiceApi --require-approval never

echo CORS fix deployment complete!
echo.
echo The following changes have been made:
echo 1. Updated Lambda function CORS headers to allow only CloudFront origin
echo 2. Updated API Gateway CORS configuration
echo.
echo Please test your application now.
pause