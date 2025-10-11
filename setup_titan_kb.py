import boto3
import json
import time

bedrock = boto3.client('bedrock-agent', region_name='us-east-1')
iam = boto3.client('iam', region_name='us-east-1')
aoss = boto3.client('opensearchserverless', region_name='us-east-1')

# Step 1: Create new OpenSearch collection
print("Creating OpenSearch collection...")
try:
    coll_response = aoss.create_collection(
        name='unifitv-kb-titan',
        type='VECTORSEARCH'
    )
    collection_id = coll_response['createCollectionDetail']['id']
    collection_arn = coll_response['createCollectionDetail']['arn']
    print(f"Collection created: {collection_id}")
    
    # Wait for collection to be active
    print("Waiting for collection to be active...")
    for i in range(60):
        time.sleep(5)
        coll = aoss.batch_get_collection(ids=[collection_id])
        if coll['collectionDetails'][0]['status'] == 'ACTIVE':
            print("Collection is active")
            break
except Exception as e:
    print(f"Collection error: {e}")
    exit(1)

# Step 2: Create IAM role
role_name = 'UnifiTV-KB-Titan-Role'
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
    print(f"Role created: {role_arn}")
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=role_name)['Role']['Arn']
    print(f"Using existing role: {role_arn}")

# Attach policies
iam.put_role_policy(
    RoleName=role_name,
    PolicyName='BedrockModelAccess',
    PolicyDocument=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
        }]
    })
)

iam.put_role_policy(
    RoleName=role_name,
    PolicyName='S3Access',
    PolicyDocument=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": [
                "arn:aws:s3:::knowledge-base-unifitv-v1",
                "arn:aws:s3:::knowledge-base-unifitv-v1/*"
            ]
        }]
    })
)

iam.put_role_policy(
    RoleName=role_name,
    PolicyName='AOSSAccess',
    PolicyDocument=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "aoss:APIAccessAll",
            "Resource": collection_arn
        }]
    })
)
print("Policies attached")

# Step 3: Create AOSS data access policy
aoss.create_access_policy(
    name='unifitv-titan-access',
    type='data',
    policy=json.dumps([{
        "Rules": [
            {
                "Resource": [f"collection/{collection_id}"],
                "Permission": ["aoss:CreateCollectionItems", "aoss:UpdateCollectionItems", "aoss:DescribeCollectionItems"],
                "ResourceType": "collection"
            },
            {
                "Resource": [f"index/{collection_id}/*"],
                "Permission": ["aoss:CreateIndex", "aoss:UpdateIndex", "aoss:DescribeIndex", "aoss:ReadDocument", "aoss:WriteDocument"],
                "ResourceType": "index"
            }
        ],
        "Principal": [role_arn]
    }])
)
print("AOSS access policy created")

time.sleep(10)

# Step 4: Create Knowledge Base
print("Creating Knowledge Base...")
kb_response = bedrock.create_knowledge_base(
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
            'collectionArn': collection_arn,
            'vectorIndexName': 'unifitv-vector-index',
            'fieldMapping': {
                'vectorField': 'vector',
                'textField': 'text',
                'metadataField': 'metadata'
            }
        }
    }
)
kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
print(f"KB created: {kb_id}")

# Step 5: Create data source
time.sleep(5)
ds_response = bedrock.create_data_source(
    knowledgeBaseId=kb_id,
    name='unifitv-docs',
    dataSourceConfiguration={
        'type': 'S3',
        's3Configuration': {
            'bucketArn': 'arn:aws:s3:::knowledge-base-unifitv-v1'
        }
    }
)
ds_id = ds_response['dataSource']['dataSourceId']
print(f"Data source created: {ds_id}")

# Step 6: Start ingestion
time.sleep(5)
ing_response = bedrock.start_ingestion_job(
    knowledgeBaseId=kb_id,
    dataSourceId=ds_id
)
job_id = ing_response['ingestionJob']['ingestionJobId']
print(f"Ingestion started: {job_id}")

# Monitor ingestion
print("\nMonitoring ingestion...")
for i in range(60):
    time.sleep(5)
    job = bedrock.get_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=ds_id,
        ingestionJobId=job_id
    )
    status = job['ingestionJob']['status']
    print(f"  [{i*5}s] {status}")
    
    if status == 'COMPLETE':
        print(f"\nSUCCESS! Update Lambda env var KNOWLEDGE_BASE_ID to: {kb_id}")
        break
    elif status == 'FAILED':
        print(f"\nFAILED: {job['ingestionJob'].get('failureReasons', [])}")
        break
