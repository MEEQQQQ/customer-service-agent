@echo off
REM Create Bedrock Guardrail for PII Protection using AWS CLI

echo Creating Bedrock Guardrail for PII Protection...

aws bedrock create-guardrail ^
  --name "tv-customer-service-pii-guard" ^
  --description "PII protection for TV customer service chatbot" ^
  --sensitive-information-policy-config file://guardrail_pii_config.json ^
  --content-policy-config file://guardrail_content_config.json ^
  --blocked-input-messaging "I cannot process requests containing sensitive financial information. Please remove credit card, SSN, or bank account numbers." ^
  --blocked-outputs-messaging "I cannot provide that information as it may contain sensitive data." ^
  --tags Key=Project,Value=CustomerServiceAgent Key=Environment,Value=Production ^
  --region us-east-1 ^
  --output json > guardrail_output.json

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Guardrail created successfully!
    echo.
    echo Extracting Guardrail ID and Version...
    
    REM Extract guardrail ID and version using PowerShell
    powershell -Command "$json = Get-Content guardrail_output.json | ConvertFrom-Json; Write-Host 'Guardrail ID:' $json.guardrailId; Write-Host 'Version:' $json.version; Write-Host ''; Write-Host 'Set these environment variables:'; Write-Host 'set GUARDRAIL_ID='$json.guardrailId; Write-Host 'set GUARDRAIL_VERSION='$json.version"
    
    echo.
    echo Full output saved to guardrail_output.json
) else (
    echo ❌ Failed to create guardrail
    echo Check your AWS credentials and permissions
)

pause
