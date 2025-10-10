import boto3
import json

bedrock = boto3.client('bedrock')

def create_pii_guardrail():
    """Create Bedrock Guardrail for PII protection"""
    
    response = bedrock.create_guardrail(
        name='tv-customer-service-pii-guard',
        description='PII protection for TV customer service chatbot',
        
        # PII entities to detect and filter
        sensitiveInformationPolicyConfig={
            'piiEntitiesConfig': [
                {'type': 'EMAIL', 'action': 'ANONYMIZE'},
                {'type': 'PHONE', 'action': 'ANONYMIZE'},
                {'type': 'NAME', 'action': 'ANONYMIZE'},
                {'type': 'ADDRESS', 'action': 'ANONYMIZE'},
                {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'BLOCK'},
                {'type': 'US_SOCIAL_SECURITY_NUMBER', 'action': 'BLOCK'},
                {'type': 'US_BANK_ACCOUNT_NUMBER', 'action': 'BLOCK'},
                {'type': 'US_PASSPORT_NUMBER', 'action': 'BLOCK'},
                {'type': 'DRIVER_ID', 'action': 'ANONYMIZE'},
            ]
        },
        
        # Content filters
        contentPolicyConfig={
            'filtersConfig': [
                {'type': 'SEXUAL', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'VIOLENCE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'HATE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'INSULTS', 'inputStrength': 'MEDIUM', 'outputStrength': 'MEDIUM'},
                {'type': 'MISCONDUCT', 'inputStrength': 'MEDIUM', 'outputStrength': 'MEDIUM'},
                {'type': 'PROMPT_ATTACK', 'inputStrength': 'HIGH', 'outputStrength': 'NONE'},
            ]
        },
        
        blockedInputMessaging='I cannot process requests containing sensitive financial information. Please remove credit card, SSN, or bank account numbers.',
        blockedOutputsMessaging='I cannot provide that information as it may contain sensitive data.',
        
        tags=[
            {'key': 'Project', 'value': 'CustomerServiceAgent'},
            {'key': 'Environment', 'value': 'Production'}
        ]
    )
    
    guardrail_id = response['guardrailId']
    guardrail_arn = response['guardrailArn']
    version = response['version']
    
    print(f"✅ Guardrail created successfully!")
    print(f"Guardrail ID: {guardrail_id}")
    print(f"Guardrail ARN: {guardrail_arn}")
    print(f"Version: {version}")
    
    # Save to config file
    config = {
        'guardrail_id': guardrail_id,
        'guardrail_version': version
    }
    
    with open('guardrail_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n📝 Configuration saved to guardrail_config.json")
    print(f"\nAdd these to your Lambda environment variables:")
    print(f"GUARDRAIL_ID={guardrail_id}")
    print(f"GUARDRAIL_VERSION={version}")
    
    return guardrail_id, version

if __name__ == '__main__':
    create_pii_guardrail()
