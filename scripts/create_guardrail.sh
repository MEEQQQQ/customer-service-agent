#!/bin/bash
# Create Bedrock Guardrail for PII Protection using AWS CLI

echo "Creating Bedrock Guardrail for PII Protection..."

aws bedrock create-guardrail \
  --name "tv-customer-service-pii-guard" \
  --description "PII protection for TV customer service chatbot" \
  --sensitive-information-policy-config file://guardrail_pii_config.json \
  --content-policy-config file://guardrail_content_config.json \
  --blocked-input-messaging "I cannot process requests containing sensitive financial information. Please remove credit card, SSN, or bank account numbers." \
  --blocked-outputs-messaging "I cannot provide that information as it may contain sensitive data." \
  --tags Key=Project,Value=CustomerServiceAgent Key=Environment,Value=Production \
  --region us-east-1 \
  --output json > guardrail_output.json

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Guardrail created successfully!"
    echo ""
    
    # Extract guardrail ID and version
    GUARDRAIL_ID=$(jq -r '.guardrailId' guardrail_output.json)
    VERSION=$(jq -r '.version' guardrail_output.json)
    
    echo "Guardrail ID: $GUARDRAIL_ID"
    echo "Version: $VERSION"
    echo ""
    echo "Set these environment variables:"
    echo "export GUARDRAIL_ID=$GUARDRAIL_ID"
    echo "export GUARDRAIL_VERSION=$VERSION"
    echo ""
    echo "Full output saved to guardrail_output.json"
else
    echo "❌ Failed to create guardrail"
    echo "Check your AWS credentials and permissions"
fi
