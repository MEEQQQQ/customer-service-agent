import json
import boto3
import os
import logging
from datetime import datetime
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
        # Check if body exists
        if not event.get('body'):
            logger.error(f"No body in request. Event: {json.dumps(event)}")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Request body is required',
                    'message': 'No data provided'
                })
            }
        
        body = json.loads(event['body'])
        logger.info(f"Received feedback request: {json.dumps(body)}")
        
        session_id = body.get('session_id', 'unknown')
        vote_type = body.get('vote_type', 'positive')
        username = body.get('username', 'user')
        feedback_text = body.get('feedback_text', '')
        message_id = body.get('message_id', f'msg_{int(datetime.utcnow().timestamp() * 1000)}')
        
        # Create unique identifier: session_message for partition key
        # This allows multiple feedback entries per session (one per message)
        feedback_id = f"{session_id}_{message_id}"
        
        item = {
            'username': feedback_id,  # Using username field as partition key per existing schema
            'vote_type': vote_type,
            'session_id': session_id,
            'message_id': message_id,
            'feedback_text': feedback_text,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Writing to DynamoDB table: {table.table_name}")
        logger.info(f"Item to write: {json.dumps(item, default=str)}")
        
        table.put_item(Item=item)
        logger.info(f"Successfully wrote feedback for session {session_id}, message {message_id}")
        
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
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Invalid JSON format',
                'message': str(e)
            })
        }
    except Exception as e:
        logger.error(f"Feedback submission failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to save feedback'
            })
        }
