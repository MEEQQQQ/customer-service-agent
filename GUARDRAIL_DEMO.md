# Bedrock Guardrails Demo Guide

## Overview
This guide shows how to demonstrate PII protection using Bedrock Guardrails in your TV customer service chatbot.

## Current Guardrail Configuration
- **Guardrail ID**: `5dlelmx343n1`
- **Version**: `1`
- **Status**: `READY`

## Demo Scenarios

### 1. Email Anonymization (ANONYMIZE)

**Test Input:**
```
"My email is john.doe@example.com and I need help with my TV"
```

**Expected Behavior:**
- Guardrail detects EMAIL
- Replaces with `[EMAIL]` before sending to model
- Model receives: "My email is [EMAIL] and I need help with my TV"
- Response is normal troubleshooting help

**How to Demo:**
1. Open chatbot
2. Type: "My email is support@customer.com, can you help?"
3. Show that conversation continues normally
4. Check CloudWatch logs for: `Using Guardrail: 5dlelmx343n1 v1`

---

### 2. Phone Number Anonymization (ANONYMIZE)

**Test Input:**
```
"Call me at +1-555-123-4567 if you need more info"
```

**Expected Behavior:**
- Guardrail detects PHONE
- Replaces with `[PHONE]`
- Model receives: "Call me at [PHONE] if you need more info"

**How to Demo:**
1. Type: "My phone is 555-1234, please call me"
2. Conversation continues
3. PII is masked but request is processed

---

### 3. Credit Card Blocking (BLOCK)

**Test Input:**
```
"My credit card 4532-1234-5678-9010 was charged incorrectly"
```

**Expected Behavior:**
- Guardrail detects CREDIT_CARD
- **BLOCKS entire request**
- User receives: "I cannot process this request as it contains sensitive information. Please remove any credit card numbers, SSN, or bank account details and try again."
- Request never reaches the model

**How to Demo:**
1. Type: "My card number is 4532123456789010"
2. Show error message appears
3. Check CloudWatch logs for: `🛡️ Guardrail blocked request`
4. Explain: "The system protected your sensitive data"

---

### 4. SSN Blocking (BLOCK)

**Test Input:**
```
"My SSN is 123-45-6789 and I need service"
```

**Expected Behavior:**
- Guardrail detects SSN
- **BLOCKS entire request**
- Same error message as credit card

**How to Demo:**
1. Type: "My social security number is 123-45-6789"
2. Request is blocked
3. Show protection message

---

### 5. Multiple PII Anonymization

**Test Input:**
```
"I'm John Smith, email john@test.com, phone 555-9876"
```

**Expected Behavior:**
- Guardrail detects: NAME, EMAIL, PHONE
- All replaced: "I'm [NAME], email [EMAIL], phone [PHONE]"
- Model processes anonymized version

**How to Demo:**
1. Type: "I'm Jane Doe, contact me at jane@email.com or 555-1234"
2. Show conversation continues
3. All PII is masked

---

### 6. Name Anonymization in Context

**Test Input:**
```
"Hi, I'm Michael Johnson and my TV isn't working"
```

**Expected Behavior:**
- Guardrail detects NAME
- Replaces with `[NAME]`
- Model receives: "Hi, I'm [NAME] and my TV isn't working"

---

## Demo Script for Presentation

### Setup (Before Demo)
1. Ensure guardrail is deployed:
   ```bash
   aws bedrock get-guardrail --guardrail-identifier 5dlelmx343n1 --region us-east-1
   ```
2. Set environment variables:
   ```bash
   set GUARDRAIL_ID=5dlelmx343n1
   set GUARDRAIL_VERSION=1
   ```
3. Deploy application:
   ```bash
   cdk deploy
   ```

### Live Demo Flow

**Step 1: Normal Conversation (No PII)**
```
User: "My TV has no signal"
Bot: [Normal troubleshooting response]
```
*Explain: "Normal operation without sensitive data"*

---

**Step 2: Email Protection (Anonymized)**
```
User: "My email is demo@example.com, can you help?"
Bot: [Normal response, email was masked]
```
*Explain: "Email was detected and anonymized to [EMAIL] before processing"*

*Show CloudWatch Logs:*
```
Using Guardrail: 5dlelmx343n1 v1
Input: "My email is demo@example.com..."
Processed: "My email is [EMAIL]..."
```

---

**Step 3: Credit Card Protection (Blocked)**
```
User: "My card 4532-1234-5678-9010 was charged"
Bot: "I cannot process this request as it contains sensitive information..."
```
*Explain: "Credit card detected - request completely blocked for security"*

*Show CloudWatch Logs:*
```
🛡️ Guardrail blocked request: ValidationException
```

---

**Step 4: Multiple PII (Anonymized)**
```
User: "I'm John Doe, email john@test.com, phone 555-1234"
Bot: [Normal response]
```
*Explain: "All three PII types (name, email, phone) were anonymized"*

---

## Verification Methods

### Method 1: CloudWatch Logs
```bash
aws logs tail /aws/lambda/CustomerServiceApi-BedrockHandler --follow
```

Look for:
- `Using Guardrail: 5dlelmx343n1 v1`
- `⚠️ Guardrail action taken: GUARDRAIL_INTERVENED`
- `🛡️ Guardrail blocked request`

### Method 2: Check Response
- Blocked requests return specific error message
- Anonymized requests process normally
- Check response doesn't contain original PII

### Method 3: DynamoDB Ticket Log
```bash
aws dynamodb scan --table-name ticket_log --region us-east-1
```
- Check if PII is stored (it shouldn't be)
- Verify only anonymized data is saved

---

## Test Cases Summary

| Test Case | Input Example | Action | Expected Result |
|-----------|---------------|--------|-----------------|
| Email | `john@example.com` | ANONYMIZE | `[EMAIL]` |
| Phone | `555-123-4567` | ANONYMIZE | `[PHONE]` |
| Name | `John Smith` | ANONYMIZE | `[NAME]` |
| Address | `123 Main St` | ANONYMIZE | `[ADDRESS]` |
| Credit Card | `4532-1234-5678-9010` | BLOCK | Error message |
| SSN | `123-45-6789` | BLOCK | Error message |
| Bank Account | `123456789012` | BLOCK | Error message |
| Passport | `A12345678` | BLOCK | Error message |
| Driver License | `D1234567` | ANONYMIZE | `[DRIVER_ID]` |

---

## Presentation Talking Points

1. **Security First**: "Our system automatically protects customer data using AWS Bedrock Guardrails"

2. **Two-Layer Protection**:
   - Input filtering: "PII is detected before reaching the AI model"
   - Output filtering: "Responses are scanned to prevent data leakage"

3. **Smart Handling**:
   - "Non-critical PII like email is anonymized but conversation continues"
   - "Critical PII like credit cards completely blocks the request"

4. **Compliance**: "Helps meet GDPR, CCPA, and other privacy regulations"

5. **Zero Code Changes**: "Protection is applied automatically without modifying application logic"

---

## Troubleshooting Demo Issues

### Guardrail Not Working
```bash
# Check if guardrail is active
aws bedrock get-guardrail --guardrail-identifier 5dlelmx343n1 --region us-east-1

# Verify environment variables
echo $GUARDRAIL_ID
echo $GUARDRAIL_VERSION
```

### PII Not Detected
- Use clear, standard formats (e.g., `john@example.com` not `john at example dot com`)
- Phone: `555-123-4567` or `+1-555-123-4567`
- Credit Card: `4532-1234-5678-9010` or `4532123456789010`

### Check Logs
```bash
aws logs tail /aws/lambda/CustomerServiceApi-BedrockHandler --since 5m
```

---

## Quick Demo Commands

**Test Email:**
```bash
curl -X POST https://your-api.amazonaws.com/prod/troubleshoot \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-123","text":"My email is test@example.com"}'
```

**Test Credit Card (Should Block):**
```bash
curl -X POST https://your-api.amazonaws.com/prod/troubleshoot \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-123","text":"My card is 4532123456789010"}'
```

---

## Cost of Guardrails

- **$0.75 per 1,000 text units** (1 unit = 1,000 characters)
- Example: 1,000 messages × 500 chars = 500,000 chars = $0.375
- Minimal cost for enterprise-grade PII protection

---

## Benefits Highlight

✅ **Automatic PII Detection** - No manual coding needed
✅ **Real-time Protection** - Works on every request
✅ **Compliance Ready** - Meets privacy regulations
✅ **Flexible Policies** - Anonymize or block based on sensitivity
✅ **Audit Trail** - All actions logged in CloudWatch
✅ **Zero Downtime** - Can be enabled/disabled without redeployment
