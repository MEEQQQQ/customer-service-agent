@echo off
echo Updating Bedrock Guardrail...

set GUARDRAIL_ID=5dlelmx343n1
set REGION=us-east-1

echo Step 1: Updating guardrail configuration...

aws bedrock update-guardrail ^
  --guardrail-identifier %GUARDRAIL_ID% ^
  --name "CustomerServiceGuardrail" ^
  --description "Protects against PII and inappropriate content" ^
  --content-policy-config "filtersConfig=[{type=SEXUAL,inputStrength=HIGH,outputStrength=HIGH},{type=VIOLENCE,inputStrength=HIGH,outputStrength=HIGH},{type=HATE,inputStrength=HIGH,outputStrength=HIGH},{type=INSULTS,inputStrength=HIGH,outputStrength=HIGH},{type=MISCONDUCT,inputStrength=MEDIUM,outputStrength=MEDIUM},{type=PROMPT_ATTACK,inputStrength=HIGH,outputStrength=NONE}]" ^
  --sensitive-information-policy-config "piiEntitiesConfig=[{type=EMAIL,action=ANONYMIZE},{type=PHONE,action=ANONYMIZE},{type=NAME,action=ANONYMIZE},{type=ADDRESS,action=ANONYMIZE},{type=CREDIT_DEBIT_CARD_NUMBER,action=BLOCK},{type=US_SOCIAL_SECURITY_NUMBER,action=BLOCK},{type=US_BANK_ACCOUNT_NUMBER,action=BLOCK},{type=US_PASSPORT_NUMBER,action=BLOCK},{type=DRIVER_ID,action=ANONYMIZE}]" ^
  --word-policy-config "wordsConfig=[{text=fuck},{text=shit},{text=bitch},{text=asshole},{text=damn},{text=bastard}],managedWordListsConfig=[{type=PROFANITY}]" ^
  --blocked-input-messaging "Hey! I noticed your message might have some sensitive info or inappropriate content. For your security and to keep things professional, could you rephrase that? I'm here to help with your TV issue!" ^
  --blocked-outputs-messaging "Oops, I can't share that info. But I'm happy to help with your TV service in another way - what do you need?" ^
  --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo Error updating guardrail!
    exit /b 1
)

echo.
echo Step 2: Creating new guardrail version...

aws bedrock create-guardrail-version ^
  --guardrail-identifier %GUARDRAIL_ID% ^
  --description "Updated with conversational blocked messages" ^
  --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo Error creating guardrail version!
    exit /b 1
)

echo.
echo ========================================
echo Guardrail updated successfully!
echo ========================================
echo.
echo IMPORTANT: Update Lambda environment variable GUARDRAIL_VERSION
echo Run: aws lambda update-function-configuration --function-name bedrock-handler --environment Variables={GUARDRAIL_VERSION=NEW_VERSION}
echo.
