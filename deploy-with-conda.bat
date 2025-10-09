@echo off
echo Deploying Customer Service Agent with Conda Environment...

echo.
echo Step 1: Activating conda environment 'customer-service'
call conda activate customer-service

echo.
echo Step 2: Verifying Python installation
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in conda environment
    echo Please make sure the 'customer-service' conda environment is created and has Python installed
    pause
    exit /b 1
)

echo.
echo Step 3: Installing/updating Python dependencies
pip install -r requirements.txt

echo.
echo Step 4: Checking CDK installation
cdk --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CDK not found. Installing CDK...
    npm install -g aws-cdk
)

echo.
echo Step 5: Bootstrapping CDK (if needed)
echo This will create necessary CDK resources in your AWS account
cdk bootstrap

echo.
echo Step 6: Deploying stacks
echo Deploying Core stack...
cdk deploy CustomerServiceCore --require-approval never

echo.
echo Deploying API stack...
cdk deploy CustomerServiceApi --require-approval never

echo.
echo Deploying Web stack...
cdk deploy CustomerServiceWeb --require-approval never

echo.
echo Deployment complete! Your CORS issues should now be resolved.
echo Check the output above for any API Gateway URLs.

pause