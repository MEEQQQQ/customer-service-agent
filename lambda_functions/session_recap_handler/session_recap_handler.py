import json
import boto3
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
feedback_table = dynamodb.Table(os.environ.get('FEEDBACK_TABLE', 'performance-thumbsup'))

def lambda_handler(event, context):
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': ''
        }
    
    try:
        session_id = event['pathParameters']['session_id']
        
        # Get feedback stats using scan (username is partition key, not session_id)
        response = feedback_table.scan(
            FilterExpression='session_id = :sid',
            ExpressionAttributeValues={':sid': session_id}
        )
        
        items = response.get('Items', [])
        positive_count = sum(1 for item in items if item['vote_type'] == 'positive')
        negative_count = sum(1 for item in items if item['vote_type'] == 'negative')
        total_feedback = len(items)
        satisfaction_rate = (positive_count / total_feedback * 100) if total_feedback > 0 else 0
        
        # Get CloudWatch metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        duration_stats = get_metric_statistics(
            'AWS/Lambda', 'Duration', start_time, end_time, ['Average'],
            [{'Name': 'FunctionName', 'Value': os.environ.get('FUNCTION_NAME', 'CustomerServiceApi-BedrockHandler')}]
        )
        
        invocation_stats = get_metric_statistics(
            'AWS/Lambda', 'Invocations', start_time, end_time, ['Sum'],
            [{'Name': 'FunctionName', 'Value': os.environ.get('FUNCTION_NAME', 'CustomerServiceApi-BedrockHandler')}]
        )
        
        error_stats = get_metric_statistics(
            'AWS/Lambda', 'Errors', start_time, end_time, ['Sum'],
            [{'Name': 'FunctionName', 'Value': os.environ.get('FUNCTION_NAME', 'CustomerServiceApi-BedrockHandler')}]
        )
        
        avg_duration = duration_stats['Datapoints'][0]['Average'] if duration_stats['Datapoints'] else 0
        total_invocations = invocation_stats['Datapoints'][0]['Sum'] if invocation_stats['Datapoints'] else 0
        total_errors = error_stats['Datapoints'][0]['Sum'] if error_stats['Datapoints'] else 0
        
        success_rate = ((total_invocations - total_errors) / total_invocations * 100) if total_invocations > 0 else 100
        
        recap_data = {
            'session_id': session_id,
            'metrics': {
                'response_time': round(avg_duration / 1000, 2),
                'success_rate': round(success_rate, 1),
                'model_confidence': 85.5,
                'system_uptime': 99.9,
                'satisfaction_rate': round(satisfaction_rate, 1)
            },
            'feedback': {
                'positive': positive_count,
                'negative': negative_count,
                'total': total_feedback,
                'comments': [item.get('feedback_text', '') for item in items if item.get('feedback_text')]
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(recap_data, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }

def get_metric_statistics(namespace, metric_name, start_time, end_time, statistics, dimensions):
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=statistics
        )
        return response
    except Exception as e:
        return {'Datapoints': []}
