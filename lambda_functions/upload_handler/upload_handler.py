import json
import boto3
import base64
import uuid
import os
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET_NAME = os.environ['STORAGE_BUCKET']
TICKET_TABLE = os.environ.get('TICKET_TABLE', 'ticket_log')

def lambda_handler(event, context):
    # Handle CORS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    try:
        logger.info(f"Processing upload request")
        body = json.loads(event['body'])
        
        # Use existing session_id if provided, otherwise generate new one
        session_id = body.get('session_id', str(uuid.uuid4()))
        is_new_session = 'session_id' not in body
        
        # Only create ticket for new sessions
        if is_new_session:
            ticket_id = f"TKT{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        else:
            ticket_id = None
        
        timestamp = datetime.utcnow().isoformat()
        
        # Handle image upload
        image_key = None
        if 'image' in body:
            image_data = base64.b64decode(body['image'])
            image_key = f"sessions/{session_id}/image.jpg"
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=image_key,
                Body=image_data,
                ContentType='image/jpeg'
            )
        
        # Handle audio upload with timestamp to prevent caching
        audio_key = None
        if 'audio' in body:
            audio_data = base64.b64decode(body['audio'])
            audio_timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            audio_key = f"sessions/{session_id}/audio_{audio_timestamp}.wav"
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=audio_key,
                Body=audio_data,
                ContentType='audio/wav'
            )
        
        # Handle text-only requests by creating default transcript
        if not audio_key and not image_key:
            # Create a default transcript for text-only queries
            default_transcript = {
                'text': body.get('text', 'General troubleshooting request'),
                'timestamp': timestamp
            }
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=f"sessions/{session_id}/transcript.json",
                Body=json.dumps(default_transcript),
                ContentType='application/json'
            )
            
            # Create default image analysis for consistency
            default_analysis = {
                'labels': [],
                'extracted_text': [],
                'custom_labels': [],
                'tv_error_detection': [],
                'timestamp': timestamp
            }
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=f"sessions/{session_id}/image_analysis.json",
                Body=json.dumps(default_analysis),
                ContentType='application/json'
            )
        
        # Create ticket in DynamoDB only for new sessions
        if is_new_session:
            table = dynamodb.Table(TICKET_TABLE)
            table.put_item(
                Item={
                    'ticket_id': ticket_id,
                    'session_id': session_id,
                    'created_at': timestamp,
                    'status': 'open',
                    'has_image': image_key is not None,
                    'has_audio': audio_key is not None
                }
            )
            logger.info(f"Ticket created: {ticket_id}")
        else:
            logger.info(f"Uploading to existing session: {session_id}")
        
        # Store or update session metadata
        try:
            # Try to get existing metadata
            metadata_obj = s3_client.get_object(
                Bucket=BUCKET_NAME,
                Key=f"sessions/{session_id}/metadata.json"
            )
            session_data = json.loads(metadata_obj['Body'].read())
            logger.info(f"Updating existing metadata for session {session_id}")
        except:
            # Create new metadata if doesn't exist
            session_data = {
                'session_id': session_id,
                'ticket_id': ticket_id,
                'timestamp': timestamp,
                'status': 'uploaded'
            }
            logger.info(f"Creating new metadata for session {session_id}")
        
        # Update with new file keys
        if image_key:
            session_data['image_key'] = image_key
        if audio_key:
            session_data['audio_key'] = audio_key
            session_data['latest_audio_key'] = audio_key
        session_data['last_updated'] = timestamp
        
        # Save metadata
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f"sessions/{session_id}/metadata.json",
            Body=json.dumps(session_data),
            ContentType='application/json'
        )
        
        logger.info(f"Upload successful for session: {session_id}")
        response_body = {
            'session_id': session_id,
            'message': 'Files uploaded successfully'
        }
        if ticket_id:
            response_body['ticket_id'] = ticket_id
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Upload failed',
                'details': str(e)
            })
        }