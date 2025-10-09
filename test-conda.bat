@echo off
echo Testing conda environment setup...

echo.
echo Activating conda environment 'customer-service'
call conda activate customer-service

echo.
echo Testing Python:
python --version
python -c "import sys; print('Python executable:', sys.executable)"

echo.
echo Testing required packages:
python -c "import boto3; print('boto3 version:', boto3.__version__)"
python -c "import aws_cdk; print('CDK version:', aws_cdk.__version__)"

echo.
echo Testing CDK:
cdk --version

echo.
echo If all tests pass, you can run: deploy-with-conda.bat
pause