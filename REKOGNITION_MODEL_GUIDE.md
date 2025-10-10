# Rekognition Custom Model Guide

## Issue
Your custom Rekognition model returns empty results (`tv_error_detection: []`)

## Root Causes

### 1. Model is Running ✅
The model `arn:aws:rekognition:us-east-1:190403256083:project/tv-error-detection/version/v1/1760113338518` is RUNNING.

### 2. Possible Reasons for Empty Results:

**A. Image doesn't match training data**
- Your model was trained on TV error screens
- You uploaded a phone screenshot showing "Update Your Contact Details"
- This is NOT a TV error screen, so the model correctly returns no matches

**B. Confidence threshold too high**
- Was set to 50% minimum confidence
- Lowered to 30% for better detection

## Solution Applied

### Updated image_analysis_handler.py:
1. Lowered `MinConfidence` from 50 to 30
2. Added detailed logging to track detection results
3. Added warning when no labels detected

## How to Test

### Test with actual TV error image:
1. Upload an image showing a TV error screen (e.g., "No Signal", "HDMI Error", etc.)
2. The model should detect it if it was trained on similar errors

### Check what your model was trained on:
```bash
aws rekognition describe-project-versions \
  --project-arn "arn:aws:rekognition:us-east-1:190403256083:project/tv-error-detection/1760113338518" \
  --region us-east-1
```

## Model Management

### Start Model:
```bash
aws rekognition start-project-version \
  --project-version-arn "arn:aws:rekognition:us-east-1:190403256083:project/tv-error-detection/version/v1/1760113338518" \
  --min-inference-units 1 \
  --region us-east-1
```

### Stop Model (to save costs):
```bash
aws rekognition stop-project-version \
  --project-version-arn "arn:aws:rekognition:us-east-1:190403256083:project/tv-error-detection/version/v1/1760113338518" \
  --region us-east-1
```

### Check Status:
```bash
aws rekognition describe-project-versions \
  --project-arn "arn:aws:rekognition:us-east-1:190403256083:project/tv-error-detection/1760113338518" \
  --region us-east-1 \
  --query "ProjectVersionDescriptions[0].Status"
```

## Cost Note
⚠️ Running Rekognition custom models costs money per hour. Stop the model when not in use!

## Expected Behavior
- **TV error images**: Should detect labels like "no_signal", "hdmi_error", etc.
- **Non-TV images**: Will return empty array (correct behavior)
- **Standard labels**: Always work (Electronics, Mobile Phone, etc.)
- **Text detection**: Always works (extracts text from any image)
