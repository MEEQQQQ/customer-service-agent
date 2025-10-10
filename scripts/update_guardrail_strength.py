import boto3
import json

bedrock = boto3.client('bedrock', region_name='us-east-1')

GUARDRAIL_ID = '5dlelmx343n1'

# Update guardrail with HIGH strength for insults/hate and PII blocking
response = bedrock.update_guardrail(
    guardrailIdentifier=GUARDRAIL_ID,
    name='CustomerServiceGuardrail',
    description='Protects against PII and inappropriate content',
    contentPolicyConfig={
        'filtersConfig': [
            {'type': 'SEXUAL', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'VIOLENCE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'HATE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'INSULTS', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'MISCONDUCT', 'inputStrength': 'MEDIUM', 'outputStrength': 'MEDIUM'},
            {'type': 'PROMPT_ATTACK', 'inputStrength': 'HIGH', 'outputStrength': 'NONE'}
        ]
    },
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
            {'type': 'DRIVER_ID', 'action': 'ANONYMIZE'}
        ]
    },
    wordPolicyConfig={
        'wordsConfig': [
            {'text': 'fuck'},
            {'text': 'shit'},
            {'text': 'bitch'},
            {'text': 'asshole'},
            {'text': 'damn'},
            {'text': 'bastard'}
        ],
        'managedWordListsConfig': [
            {'type': 'PROFANITY'}
        ]
    },
    blockedInputMessaging='I\'m here to provide helpful and respectful customer service. I noticed your message contains either sensitive personal information (like credit card numbers, SSN, or bank details) or inappropriate content. Please rephrase your message professionally, and I\'ll be happy to assist you with your TV service needs.',
    blockedOutputsMessaging='I apologize, but I cannot provide that response. Let me help you with your TV service issue in a professional manner.'
)

print(f"Guardrail updated: {response['guardrailId']}")
print(f"Version: {response['version']}")
print("\nCreating new version...")

# Create new version
version_response = bedrock.create_guardrail_version(
    guardrailIdentifier=GUARDRAIL_ID,
    description='Added word filters for profanity and managed profanity list'
)

print(f"\nNew version created: {version_response['version']}")
print(f"Update your Lambda environment variable GUARDRAIL_VERSION to: {version_response['version']}")
