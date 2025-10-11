import boto3
import time

bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')

print("Starting ingestion job...")
try:
    response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId='VARVMASHNX',
        dataSourceId='LZJEFLIIRD'
    )
    job_id = response['ingestionJob']['ingestionJobId']
    print(f"Ingestion job started: {job_id}")
    print(f"Status: {response['ingestionJob']['status']}")
    
    # Monitor ingestion
    print("\nMonitoring ingestion (this may take 1-2 minutes)...")
    for i in range(30):
        time.sleep(5)
        job = bedrock_agent.get_ingestion_job(
            knowledgeBaseId='VARVMASHNX',
            dataSourceId='LZJEFLIIRD',
            ingestionJobId=job_id
        )
        status = job['ingestionJob']['status']
        print(f"  [{i*5}s] Status: {status}")
        
        if status == 'COMPLETE':
            print("\nSUCCESS! Knowledge Base is ready")
            print("KB ID: VARVMASHNX")
            break
        elif status == 'FAILED':
            print(f"\nFAILED: {job['ingestionJob'].get('failureReasons', [])}")
            break
            
except Exception as e:
    print(f"Error: {e}")
