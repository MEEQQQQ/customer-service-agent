@echo off
echo SUARA Customer Service Agent - Complete Deployment

REM Set AWS credentials
set AWS_ACCESS_KEY_ID=AKIASYVHLD4JVXYBAFNY
set AWS_SECRET_ACCESS_KEY=%1
set AWS_DEFAULT_REGION=us-east-1

if "%AWS_SECRET_ACCESS_KEY%"=="" (
    echo ERROR: Please provide AWS Secret Access Key
    echo Usage: deploy.bat YOUR_SECRET_KEY
    exit /b 1
)

echo Setting up Python environment...
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo Deploying all stacks...
cdk deploy --all --require-approval never

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Deployment failed
    exit /b 1
)

echo Deployment completed successfully!
pause