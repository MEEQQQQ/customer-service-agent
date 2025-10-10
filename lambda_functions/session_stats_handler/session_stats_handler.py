import json
import boto3
import os
from datetime import datetime

s3_client = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')
BUCKET_NAME = os.environ['STORAGE_BUCKET']

def lambda_handler(event, context):
    try:
        session_id = event['pathParameters']['session_id']
        
        # Get session metadata
        metadata_obj = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=f"sessions/{session_id}/metadata.json"
        )
        metadata = json.loads(metadata_obj['Body'].read())
        
        # Count messages
        total_messages = 0
        try:
            response = s3_client.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=f"sessions/{session_id}/"
            )
            total_messages = len([obj for obj in response.get('Contents', []) if 'transcript' in obj['Key'] or 'troubleshooting' in obj['Key']])
        except:
            total_messages = 2
        
        # Count feedback
        positive_feedback = 0
        negative_feedback = 0
        try:
            feedback_response = s3_client.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=f"sessions/{session_id}/feedback/"
            )
            for obj in feedback_response.get('Contents', []):
                feedback_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                feedback_data = json.loads(feedback_obj['Body'].read())
                if feedback_data['rating'] == 'positive':
                    positive_feedback += 1
                else:
                    negative_feedback += 1
        except:
            pass
        
        # Calculate session duration
        session_start = datetime.fromisoformat(metadata['timestamp'])
        session_duration = int((datetime.utcnow() - session_start).total_seconds())
        
        # Get CloudWatch metrics for response time
        response_time_avg = 2.5
        try:
            cw_response = cloudwatch.get_metric_statistics(
                Namespace='UnifiTV/CustomerService',
                MetricName='ResponseTime',
                Dimensions=[{'Name': 'SessionId', 'Value': session_id}],
                StartTime=session_start,
                EndTime=datetime.utcnow(),
                Period=3600,
                Statistics=['Average']
            )
            if cw_response['Datapoints']:
                response_time_avg = cw_response['Datapoints'][0]['Average']
        except:
            pass
        
        stats = {
            'total_messages': total_messages,
            'response_time_avg': response_time_avg,
            'positive_feedback': positive_feedback,
            'negative_feedback': negative_feedback,
            'session_duration': session_duration
        }
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(stats)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }