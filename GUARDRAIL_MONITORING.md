# Guardrail Monitoring Guide

## Where to Monitor Guardrail Blocks

### 1. CloudWatch Logs (Primary Method)

**AWS Console:**
1. Go to: https://console.aws.amazon.com/cloudwatch/
2. Click: **Logs** → **Log groups**
3. Find: `/aws/lambda/CustomerServiceApi-BedrockHandler`
4. Click **Search log group**

**Search Queries:**

**All Guardrail Activity:**
```
fields @timestamp, @message
| filter @message like /Guardrail/
| sort @timestamp desc
```

**Blocked Requests Only:**
```
fields @timestamp, @message
| filter @message like /blocked request/
| sort @timestamp desc
```

**Insult Detection:**
```
fields @timestamp, @message
| filter @message like /INSULTS/
| sort @timestamp desc
```

---

### 2. AWS CLI Monitoring

**Real-time tail:**
```bash
aws logs tail /aws/lambda/CustomerServiceApi-BedrockHandler --follow --region us-east-1
```

**Filter for guardrail events:**
```bash
aws logs tail /aws/lambda/CustomerServiceApi-BedrockHandler --follow --filter-pattern "Guardrail" --region us-east-1
```

**Get last 50 blocked requests:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/CustomerServiceApi-BedrockHandler \
  --filter-pattern "blocked request" \
  --max-items 50 \
  --region us-east-1
```

---

### 3. Test Insult Blocking

**Test Cases:**

| Input | Expected Result | Log Entry |
|-------|----------------|-----------|
| "You are stupid" | Blocked | `🛡️ Guardrail blocked request` |
| "This service sucks" | Blocked | `INSULTS filter triggered` |
| "You're an idiot" | Blocked | `ValidationException` |
| "I hate this" | May pass (LOW strength) | No block |

**Test in Chat:**
```
User: "You are stupid and useless"
Bot: "I cannot process this request..."
```

**Check Logs:**
```bash
aws logs tail /aws/lambda/CustomerServiceApi-BedrockHandler --since 1m
```

**Look for:**
```
Using Guardrail: 5dlelmx343n1 v1
🛡️ Guardrail blocked request: ValidationException
ERROR: Can't invoke 'openai.gpt-oss-120b-1:0'. Reason: ...
```

---

### 4. Create Monitoring Dashboard

**Run script:**
```bash
python scripts/create_guardrail_dashboard.py
```

**View dashboard:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=GuardrailMonitoring
```

**Dashboard shows:**
- All guardrail activity
- Blocked requests
- Lambda errors
- Invocation metrics

---

### 5. CloudWatch Insights Queries

**Query 1: Guardrail Block Rate**
```
fields @timestamp, @message
| filter @message like /Guardrail/
| stats count(*) as total_requests,
        count(@message like /blocked/) as blocked_requests
| extend block_rate = blocked_requests / total_requests * 100
```

**Query 2: Block Reasons**
```
fields @timestamp, @message
| filter @message like /blocked request/
| parse @message /blocked request: (?<reason>.*)/
| stats count() by reason
```

**Query 3: Hourly Blocks**
```
fields @timestamp
| filter @message like /blocked request/
| stats count() as blocks by bin(5m)
```

---

### 6. Set Up CloudWatch Alarms

**Create alarm for high block rate:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name GuardrailHighBlockRate \
  --alarm-description "Alert when guardrail blocks exceed threshold" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --region us-east-1
```

---

### 7. Log Entry Examples

**Successful Guardrail (Anonymized):**
```
2025-01-10 12:34:56 INFO Using Guardrail: 5dlelmx343n1 v1
2025-01-10 12:34:56 INFO Input: "My email is john@example.com"
2025-01-10 12:34:56 INFO Processed: "My email is [EMAIL]"
```

**Blocked Request (Insult):**
```
2025-01-10 12:35:10 INFO Using Guardrail: 5dlelmx343n1 v1
2025-01-10 12:35:10 ERROR 🛡️ Guardrail blocked request: ValidationException
2025-01-10 12:35:10 ERROR An error occurred (ValidationException) when calling the InvokeModel operation: Content policy violation detected
```

**Blocked Request (Credit Card):**
```
2025-01-10 12:36:20 INFO Using Guardrail: 5dlelmx343n1 v1
2025-01-10 12:36:20 ERROR 🛡️ Guardrail blocked request: ValidationException
2025-01-10 12:36:20 INFO Sensitive information detected: CREDIT_CARD
```

---

### 8. Monitoring Best Practices

1. **Set up log retention:**
   ```bash
   aws logs put-retention-policy \
     --log-group-name /aws/lambda/CustomerServiceApi-BedrockHandler \
     --retention-in-days 30 \
     --region us-east-1
   ```

2. **Export logs to S3 for long-term storage:**
   ```bash
   aws logs create-export-task \
     --log-group-name /aws/lambda/CustomerServiceApi-BedrockHandler \
     --from 1704067200000 \
     --to 1704153600000 \
     --destination guardrail-logs-bucket \
     --region us-east-1
   ```

3. **Create SNS alerts:**
   - Alert when block rate > 10%
   - Alert on repeated blocks from same session
   - Alert on new block types

---

### 9. Troubleshooting

**Guardrail not logging:**
```bash
# Check if guardrail is enabled
aws bedrock get-guardrail --guardrail-identifier 5dlelmx343n1 --region us-east-1

# Check Lambda environment variables
aws lambda get-function-configuration \
  --function-name CustomerServiceApi-BedrockHandler \
  --query 'Environment.Variables' \
  --region us-east-1
```

**No blocks showing:**
- Verify GUARDRAIL_ID is set
- Check guardrail status is READY
- Test with known blocked content (credit card)

---

### 10. Quick Demo Commands

**Monitor in real-time:**
```bash
# Terminal 1: Watch logs
aws logs tail /aws/lambda/CustomerServiceApi-BedrockHandler --follow

# Terminal 2: Send test request
curl -X POST https://your-api.amazonaws.com/prod/troubleshoot \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","text":"You are stupid"}'
```

**Check last 10 blocks:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/CustomerServiceApi-BedrockHandler \
  --filter-pattern "blocked request" \
  --max-items 10 \
  --region us-east-1 \
  --output table
```

---

## Summary

**Primary Monitoring Location:**
- **CloudWatch Logs** → `/aws/lambda/CustomerServiceApi-BedrockHandler`

**Key Log Patterns:**
- `Using Guardrail:` - Guardrail is active
- `🛡️ Guardrail blocked request` - Request was blocked
- `⚠️ Guardrail action taken` - PII was anonymized

**Quick Test:**
1. Type insult in chat
2. Check CloudWatch logs
3. See block message

**Dashboard:**
```bash
python scripts/create_guardrail_dashboard.py
```
