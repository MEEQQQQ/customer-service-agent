# Quick Fix Checklist ✅

## The 3 Problems & Solutions

### ✅ Problem 1: DynamoDB Not Updating (FIXED)
**Root Cause**: Lambda has no permission to write to DynamoDB  
**Fix**: Add IAM policy to feedback_handler Lambda

### ✅ Problem 2: All Metrics Show Fake Data (FIXED)
**Root Cause**: Code had hardcoded fallback values  
**Fix**: ALL metrics now use real CloudWatch data (Response Time, Success Rate, Model Confidence, System Uptime, Stats for Nerds)

### ✅ Problem 3: Session Not Creating?
**Status**: Sessions ARE working! Check browser console for session_id

---

## 🚨 CRITICAL: Do This First!

### Add IAM Permissions (5 minutes)

#### For FeedbackHandler Lambda:
```
AWS Console → Lambda → CustomerServiceApi-FeedbackHandler 
→ Configuration → Permissions → Click Role Name 
→ Add permissions → Create inline policy → JSON:
```
```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["dynamodb:PutItem", "dynamodb:GetItem"],
        "Resource": "arn:aws:dynamodb:us-east-1:190403256083:table/performance-thumbsup"
    }]
}
```

#### For SessionRecapHandler Lambda:
```
AWS Console → Lambda → CustomerServiceApi-SessionRecapHandler 
→ Configuration → Permissions → Click Role Name 
→ Add permissions → Create inline policy → JSON:
```
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["dynamodb:Scan", "dynamodb:Query"],
            "Resource": "arn:aws:dynamodb:us-east-1:190403256083:table/performance-thumbsup"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "logs:FilterLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## 📝 Update Lambda Code (10 minutes)

### 1. Update feedback_handler
- Copy: `lambda_functions/feedback_handler/feedback_handler.py`
- Paste into AWS Lambda Console
- Deploy

### 2. Update session_recap_handler  
- Copy: `lambda_functions/session_recap_handler/session_recap_handler.py`
- Paste into AWS Lambda Console
- Deploy

---

## 🧪 Test It (5 minutes)

1. **Local dev**: `cd web_client && npm run dev`
2. **Send message** → Creates session
3. **Click 👍 or 👎** on bot response
4. **Send another message** → Click 👍 or 👎 again
5. **Click "End Session"** → See recap

### Verify Success:
- **DynamoDB**: Should have 2+ new rows (one per thumbs up/down)
- **CloudWatch Logs**: `/aws/lambda/CustomerServiceApi-FeedbackHandler` shows "Successfully wrote feedback"
- **Session Recap**: Shows correct positive/negative counts
- **Stats for Nerds**: Shows real CloudWatch data (or "No data" if no recent activity)

---

## 🔍 Quick Debug

### DynamoDB still empty?
→ Check CloudWatch logs for "AccessDeniedException"  
→ IAM permissions not added correctly

### Stats for Nerds empty?
→ This is NORMAL if no activity in last hour  
→ Use chatbot for 2-3 minutes, then check again

### Session not working?
→ Open browser console (F12)  
→ Look for session_id in Network tab  
→ Should see session_id in API responses

---

## 📊 What Changed

| File | Change |
|------|--------|
| feedback_handler.py | Added logging + better error handling |
| session_recap_handler.py | Real CloudWatch data only (no mock) |
| SessionRecap.tsx | Dynamic UI for real metrics |
| api_stack.py | IAM permissions (for future CDK deploy) |

---

## ✅ Success Criteria

- [ ] IAM permissions added to both Lambdas
- [ ] Lambda code updated in AWS Console
- [ ] Can click 👍/👎 on messages
- [ ] DynamoDB shows new rows after each click
- [ ] Session recap shows accurate counts
- [ ] Stats for Nerds shows real data (or "No data available")
- [ ] No errors in CloudWatch logs

---

## 🆘 Still Not Working?

1. Check: `/aws/lambda/CustomerServiceApi-FeedbackHandler` logs
2. Look for: "AccessDeniedException" or "ValidationException"
3. Verify: Environment variable `FEEDBACK_TABLE = performance-thumbsup`
4. Test: Lambda directly with test event in AWS Console

See `FEEDBACK_TROUBLESHOOTING.md` for detailed debugging steps.
