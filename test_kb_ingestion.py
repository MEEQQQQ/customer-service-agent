import boto3
import json

# Test Cohere model access
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
try:
    response = bedrock_runtime.invoke_model(
        modelId='cohere.embed-english-v3',
        body=json.dumps({
            "texts": ["test"],
            "input_type": "search_query"
        })
    )
    print("✓ Cohere model accessible")
except Exception as e:
    print(f"✗ Cohere model error: {e}")

# Start ingestion job
bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
try:
    response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId='VARVMASHNX',
        dataSourceId='LZJEFLIIRD'
    )
    print(f"✓ Ingestion job started: {response['ingestionJob']['ingestionJobId']}")
    print(f"  Status: {response['ingestionJob']['status']}")
except Exception as e:
    print(f"✗ Ingestion job error: {e}")
