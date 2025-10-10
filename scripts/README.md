# Guardrail Setup Scripts

## Quick Start

### Windows
```bash
cd scripts
create_guardrail.bat
```

### Linux/Mac
```bash
cd scripts
chmod +x create_guardrail.sh
./create_guardrail.sh
```

## Files

- **`create_guardrail.bat`** - Windows script to create guardrail
- **`create_guardrail.sh`** - Linux/Mac script to create guardrail
- **`guardrail_pii_config.json`** - PII entity configuration
- **`guardrail_content_config.json`** - Content filter configuration
- **`setup_guardrail.py`** - Python alternative (if you prefer)

## Output

After running, you'll get:
- `guardrail_output.json` - Full AWS response
- Guardrail ID and Version printed to console

## Next Steps

1. Copy the `GUARDRAIL_ID` and `GUARDRAIL_VERSION` from output
2. Set environment variables:
   ```bash
   # Windows
   set GUARDRAIL_ID=your-id-here
   set GUARDRAIL_VERSION=1
   
   # Linux/Mac
   export GUARDRAIL_ID=your-id-here
   export GUARDRAIL_VERSION=1
   ```
3. Deploy: `cdk deploy`

## Verify Guardrail

```bash
aws bedrock get-guardrail --guardrail-identifier YOUR_GUARDRAIL_ID --region us-east-1
```

## Delete Guardrail (if needed)

```bash
aws bedrock delete-guardrail --guardrail-identifier YOUR_GUARDRAIL_ID --region us-east-1
```
