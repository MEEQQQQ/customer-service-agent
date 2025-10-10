# Test Guardrail Now

## Guardrail is NOW ACTIVE ✅

**Configuration:**
- Guardrail ID: `5dlelmx343n1`
- Version: `1`
- Status: `READY`

## Test Cases

### 1. Test Insult (Should Block)
**Type in chat:**
```
"You are stupid and useless"
```

**Expected:**
- Bot responds with error message
- CloudWatch shows: `🛡️ Guardrail blocked request`

### 2. Test Credit Card (Should Block)
**Type in chat:**
```
"My card number is 4532-1234-5678-9010"
```

**Expected:**
- Request blocked
- Error: "I cannot process this request as it contains sensitive information..."

### 3. Test Email (Should Anonymize)
**Type in chat:**
```
"My email is john@example.com"
```

**Expected:**
- Chat continues normally
- Email masked to `[EMAIL]` in backend

## Monitor in Real-Time

**Open CloudWatch Logs:**
```bash
aws logs tail /aws/lambda/CustomerServiceApi-BedrockHandler433D43D0-QBxgF1IUb9x1 --follow --region us-east-1
```

**Look for:**
```
Using Guardrail: 5dlelmx343n1 v1
🛡️ Guardrail blocked request: ValidationException
```

## Quick Test Script

```bash
# Test insult
curl -X POST https://your-api-url/prod/troubleshoot \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-123","text":"You are stupid"}'

# Watch logs
aws logs tail /aws/lambda/CustomerServiceApi-BedrockHandler433D43D0-QBxgF1IUb9x1 --since 1m --region us-east-1
```

## What Changed

**Before:**
```json
{
  "GUARDRAIL_ID": "",
  "GUARDRAIL_VERSION": "DRAFT"
}
```

**After:**
```json
{
  "GUARDRAIL_ID": "5dlelmx343n1",
  "GUARDRAIL_VERSION": "1"
}
```

## Next Steps

1. Open your chatbot
2. Type an insult or credit card number
3. Check CloudWatch logs for guardrail activity
4. See the protection in action!

The guardrail is now protecting your application! 🛡️
