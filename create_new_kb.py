import boto3
import json
import time

bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
iam = boto3.client('iam', region_name='us-east-1')

# Create IAM role for KB
role_name = 'BedrockKBRole-UnifiTV'
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "bedrock.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

try:
    role_response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    role_arn = role_response['Role']['Arn']
    print(f"Created role: {role_arn}")
    time.sleep(10)
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=role_name)['Role']['Arn']
    print(f"Using existing role: {role_arn}")

# Attach policies
policies = {
    'BedrockKBModelPolicy': {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
        }]
    },
    'BedrockKBS3Policy': {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": [
                "arn:aws:s3:::knowledge-base-unifitv-v1",
                "arn:aws:s3:::knowledge-base-unifitv-v1/*"
            ]
        }]
    },
    'BedrockKBOSSPolicy': {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["aoss:APIAccessAll"],
            "Resource": "arn:aws:aoss:us-east-1:190403256083:collection/aglxqq4cvgwcjs9c9o8b"
        }]
    }
}

for policy_name, policy_doc in policies.items():
    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_doc)
        )
        print(f"Attached policy: {policy_name}")
    except Exception as e:
        print(f"Policy {policy_name} error: {e}")

time.sleep(5)

# Create Knowledge Base
try:
    kb_response = bedrock_agent.create_knowledge_base(
        name='unifitv-kb-titan',
        roleArn=role_arn,
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
            }
        },
        storageConfiguration={
            'type': 'OPENSEARCH_SERVERLESS',
            'opensearchServerlessConfiguration': {
                'collectionArn': 'arn:aws:aoss:us-east-1:190403256083:collection/aglxqq4cvgwcjs9c9o8b',
                'vectorIndexName': 'bedrock-knowledge-base-default-index',
                'fieldMapping': {
                    'vectorField': 'bedrock-knowledge-base-default-vector',
                    'textField': 'AMAZON_BEDROCK_TEXT',
                    'metadataField': 'AMAZON_BEDROCK_METADATA'
                }
            }
        }
    )
    kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
    print(f"\n✓ Knowledge Base created: {kb_id}")
    
    # Create data source
    time.sleep(5)
    ds_response = bedrock_agent.create_data_source(
        knowledgeBaseId=kb_id,
        name='unifitv-troubleshooting-docs',
        dataSourceConfiguration={
            'type': 'S3',
            's3Configuration': {
                'bucketArn': 'arn:aws:s3:::knowledge-base-unifitv-v1'
            }
        }
    )
    ds_id = ds_response['dataSource']['dataSourceId']
    print(f"✓ Data source created: {ds_id}")
    
    # Start ingestion
    time.sleep(5)
    ing_response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=ds_id
    )
    print(f"✓ Ingestion started: {ing_response['ingestionJob']['ingestionJobId']}")
    print(f"\nUpdate Lambda env var KNOWLEDGE_BASE_ID to: {kb_id}")
    
except Exception as e:
    print(f"Error: {e}")
