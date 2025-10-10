# Bedrock Guardrails for PII Protection

## Overview
Bedrock Guardrails protect your application by detecting and filtering Personally Identifiable Information (PII) in both user inputs and model responses.

## How PII Protection Works

### 1. **Input Protection (Before Model)**
```
User: "My email is john@example.com and phone is 555-1234"
   ↓
Guardrail Detection: EMAIL, PHONE detected
   ↓
Anonymized: "My email is [EMAIL] and phone is [PHONE]"
   ↓
Sent to GPT-OSS Model
```

### 2. **Output Protection (After Model)**
```
Model Response: "Contact us at support@company.com"
   ↓
Guardrail Detection: EMAIL detected
   ↓
Redacted: "Contact us at [EMAIL]"
   ↓
Returned to User
```

### 3. **Blocking Sensitive Data**
```
User: "My credit card is 4532-1234-5678-9010"
   ↓
Guardrail Detection: CREDIT_CARD detected
   ↓
BLOCKED: "I cannot process requests containing credit card numbers"
   ↓
Request never reaches model
```

## PII Entities Protected

### Anonymized (Masked but allowed)
- **EMAIL**: john@example.com → [EMAIL]
- **PHONE**: +1-555-123-4567 → [PHONE]
- **NAME**: John Smith → [NAME]
- **ADDRESS**: 123 Main St → [ADDRESS]
- **DRIVER_ID**: D1234567 → [DRIVER_ID]

### Blocked (Request rejected)
- **CREDIT_CARD**: 4532-1234-5678-9010
- **SSN**: 123-45-6789
- **BANK_ACCOUNT**: 123456789012
- **PASSPORT**: A12345678

## Setup Instructions

### Step 1: Create Guardrail Using AWS CLI

**Windows:**
```bash
cd customer-service-agent\scripts
create_guardrail.bat
```

**Linux/Mac:**
```bash
cd customer-service-agent/scripts
chmod +x create_guardrail.sh
./create_guardrail.sh
```

**Manual AWS CLI Command:**
```bash
aws bedrock create-guardrail \
  --name "tv-customer-service-pii-guard" \
  --description "PII protection for TV customer service chatbot" \
  --sensitive-information-policy-config file://guardrail_pii_config.json \
  --content-policy-config file://guardrail_content_config.json \
  --blocked-input-messaging "I cannot process requests containing sensitive financial information." \
  --blocked-outputs-messaging "I cannot provide that information as it may contain sensitive data." \
  --region us-east-1
```

This creates a guardrail and outputs:
```
✅ Guardrail created successfully!
Guardrail ID: abc123xyz
Version: 1

Set these environment variables:
set GUARDRAIL_ID=abc123xyz
set GUARDRAIL_VERSION=1
```

### Step 2: Set Environment Variables
```bash
# Windows
set GUARDRAIL_ID=abc123xyz
set GUARDRAIL_VERSION=1

# Linux/Mac
export GUARDRAIL_ID=abc123xyz
export GUARDRAIL_VERSION=1
```

### Step 3: Deploy
```bash
cdk deploy
```

### Step 4: Grant Bedrock Permissions
Add to Lambda execution role:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:ApplyGuardrail"
  ],
  "Resource": [
    "arn:aws:bedrock:*:*:guardrail/*"
  ]
}
```

## Testing PII Protection

### Test 1: Email Anonymization
**Input**: "My email is customer@example.com"
**Expected**: Model receives "My email is [EMAIL]"

### Test 2: Credit Card Blocking
**Input**: "My card number is 4532-1234-5678-9010"
**Expected**: "I cannot process requests containing sensitive financial information"

### Test 3: Multiple PII
**Input**: "I'm John Smith, email john@test.com, phone 555-1234"
**Expected**: Model receives "I'm [NAME], email [EMAIL], phone [PHONE]"

## Configuration Options

### Action Types
- **ANONYMIZE**: Replace with placeholder (e.g., [EMAIL])
- **BLOCK**: Reject entire request

### Strength Levels
- **HIGH**: Very strict filtering
- **MEDIUM**: Balanced approach
- **LOW**: Minimal filtering
- **NONE**: No filtering

### Content Filters
- **SEXUAL**: Block inappropriate content
- **VIOLENCE**: Block violent content
- **HATE**: Block hate speech
- **INSULTS**: Block insults
- **MISCONDUCT**: Block unethical content
- **PROMPT_ATTACK**: Block prompt injection attempts

## Monitoring

### CloudWatch Logs
Check Lambda logs for:
```
Using Guardrail: abc123xyz v1
⚠️ Guardrail action taken: GUARDRAIL_INTERVENED
🛡️ Guardrail blocked request: ValidationException
```

### Metrics
- `GuardrailIntervention`: Count of PII detections
- `GuardrailBlocked`: Count of blocked requests
- `GuardrailAnonymized`: Count of anonymized entities

## Cost
- **$0.75 per 1,000 text units** (1 unit = 1,000 characters)
- Example: 100 messages/day × 500 chars = 50,000 chars = $0.0375/day

## Best Practices

1. **Test thoroughly** before production
2. **Monitor logs** for false positives
3. **Adjust strength** based on use case
4. **Document** what PII is protected
5. **Train users** on what data to avoid sharing

## Troubleshooting

### Guardrail not working
- Check `GUARDRAIL_ID` and `GUARDRAIL_VERSION` are set
- Verify IAM permissions include `bedrock:ApplyGuardrail`
- Ensure guardrail is in `READY` state

### Too many false positives
- Lower strength from HIGH to MEDIUM
- Change action from BLOCK to ANONYMIZE
- Adjust specific PII entity configurations

### Performance issues
- Guardrails add ~100-200ms latency
- Consider caching for repeated queries
- Use async processing for non-critical paths
