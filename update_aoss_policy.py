import boto3
import json

aoss = boto3.client('opensearchserverless', region_name='us-east-1')

collection_id = 'aglxqq4cvgwcjs9c9o8b'
policy_name = 'unifitv-kb-access'

# Create data access policy
policy = [{
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
    "Principal": [
        "arn:aws:iam::190403256083:role/BedrockKBRole-UnifiTV",
        "arn:aws:iam::190403256083:role/service-role/AmazonBedrockExecutionRoleForKnowledgeBase_gy1li"
    ]
}]

try:
    response = aoss.create_access_policy(
        name=policy_name,
        type='data',
        policy=json.dumps(policy)
    )
    print(f"Created access policy: {policy_name}")
except aoss.exceptions.ConflictException:
    response = aoss.update_access_policy(
        name=policy_name,
        type='data',
        policyVersion='',
        policy=json.dumps(policy)
    )
    print(f"Updated access policy: {policy_name}")
except Exception as e:
    print(f"Error: {e}")
