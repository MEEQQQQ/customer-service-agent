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
BUCKET_NAME = os.environ['STORAGE_BUCKET']

def lambda_handler(event, context):
    # Handle CORS preflight requests
    if event['httpMethod'] == 'OPTIONS':
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
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
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
        
        # Handle audio upload
        audio_key = None
        if 'audio' in body:
            audio_data = base64.b64decode(body['audio'])
            audio_key = f"sessions/{session_id}/audio.wav"
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
        
        # Store session metadata
        session_data = {
            'session_id': session_id,
            'timestamp': timestamp,
            'image_key': image_key,
            'audio_key': audio_key,
            'status': 'uploaded'
        }
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f"sessions/{session_id}/metadata.json",
            Body=json.dumps(session_data),
            ContentType='application/json'
        )
        
        logger.info(f"Upload successful for session: {session_id}")
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'session_id': session_id,
                'message': 'Files uploaded successfully'
            })
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Upload failed'
            })
        }