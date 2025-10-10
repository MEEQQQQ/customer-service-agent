import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('FEEDBACK_TABLE', 'performance-thumbsup'))

def lambda_handler(event, context):
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': ''
        }
    
    try:
        body = json.loads(event['body'])
        session_id = body['session_id']
        vote_type = body['vote_type']  # 'positive' or 'negative'
        username = body.get('username', 'anonymous')
        feedback_text = body.get('feedback_text', '')
        
        item = {
            'session_id': session_id,
            'username': username,
            'vote_type': vote_type,
            'feedback_text': feedback_text,
            'timestamp': datetime.utcnow().isoformat(),
            'created_at': int(datetime.utcnow().timestamp())
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Feedback recorded successfully'
            })
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
