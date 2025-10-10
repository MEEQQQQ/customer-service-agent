import json
import boto3
import os
import re
import logging
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

rekognition_client = boto3.client('rekognition')
s3_client = boto3.client('s3')
BUCKET_NAME = os.environ['STORAGE_BUCKET']
REKOGNITION_PROJECT_ARN = os.environ.get('REKOGNITION_PROJECT_ARN')

def sanitize_session_id(session_id):
    """Sanitize session_id to prevent path traversal attacks"""
    # Only allow alphanumeric characters and hyphens
    if not re.match(r'^[a-zA-Z0-9-]+$', session_id):
        raise ValueError("Invalid session ID format")
    return session_id

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
        logger.info("Processing image analysis request")
        body = json.loads(event['body'])
        
        if 'session_id' not in body:
            raise ValueError("Missing session_id in request")
            
        session_id = sanitize_session_id(body['session_id'])
        image_key = f"sessions/{session_id}/image.jpg"
        
        # Check if image exists
        try:
            s3_client.head_object(Bucket=BUCKET_NAME, Key=image_key)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # No image file, return empty analysis
                default_analysis = {
                    'labels': [],
                    'extracted_text': [],
                    'custom_labels': [],
                    'text_detections': [],
                    'tv_error_detection': []
                }
                s3_client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=f"sessions/{session_id}/image_analysis.json",
                    Body=json.dumps(default_analysis),
                    ContentType='application/json'
                )
                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'analysis': default_analysis,
                        'session_id': session_id
                    })
                }
            else:
                raise e
        
        analysis_results = {}
        
        # TV Error Detection using specific model
        tv_error_arn = "arn:aws:rekognition:us-east-1:190403256083:project/tv-error-detection/version/v1/1760113338518"
        try:
            logger.info(f"Calling TV error detection model: {tv_error_arn}")
            tv_error_response = rekognition_client.detect_custom_labels(
                ProjectVersionArn=tv_error_arn,
                Image={
                    'S3Object': {
                        'Bucket': BUCKET_NAME,
                        'Name': image_key
                    }
                },
                MinConfidence=30  # Lowered from 50 to 30
            )
            analysis_results['tv_error_detection'] = tv_error_response.get('CustomLabels', [])
            logger.info(f"TV error detection completed for session: {session_id}, found {len(analysis_results['tv_error_detection'])} labels")
            if analysis_results['tv_error_detection']:
                logger.info(f"Detected labels: {[label['Name'] for label in analysis_results['tv_error_detection']]}")
            else:
                logger.warning(f"No TV errors detected in image (confidence threshold: 30)")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotReadyException':
                logger.warning(f"TV error detection model not running: {tv_error_arn}")
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid TV error detection model ARN: {tv_error_arn}")
            else:
                logger.error(f"TV error detection failed with {error_code}: {e}")
            analysis_results['tv_error_detection'] = []
        except Exception as e:
            logger.error(f"TV error detection failed: {e}", exc_info=True)
            analysis_results['tv_error_detection'] = []
        
        # Try custom labels (if project is trained)
        try:
            if REKOGNITION_PROJECT_ARN and REKOGNITION_PROJECT_ARN != "PLACEHOLDER_PROJECT_ARN":
                custom_response = rekognition_client.detect_custom_labels(
                    ProjectVersionArn=REKOGNITION_PROJECT_ARN,
                    Image={
                        'S3Object': {
                            'Bucket': BUCKET_NAME,
                            'Name': image_key
                        }
                    },
                    MinConfidence=70
                )
                analysis_results['custom_labels'] = custom_response.get('CustomLabels', [])
        except Exception as e:
            print(f"Custom labels detection failed: {e}")
            analysis_results['custom_labels'] = []
        
        # Fallback to standard label detection
        labels_response = rekognition_client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': BUCKET_NAME,
                    'Name': image_key
                }
            },
            MaxLabels=20,
            MinConfidence=70
        )
        analysis_results['labels'] = labels_response.get('Labels', [])
        
        # Text detection for error messages
        text_response = rekognition_client.detect_text(
            Image={
                'S3Object': {
                    'Bucket': BUCKET_NAME,
                    'Name': image_key
                }
            }
        )
        analysis_results['text_detections'] = text_response.get('TextDetections', [])
        
        # Extract meaningful text
        detected_text = []
        for text_detection in analysis_results['text_detections']:
            if text_detection['Type'] == 'LINE' and text_detection['Confidence'] > 80:
                detected_text.append(text_detection['DetectedText'])
        
        analysis_results['extracted_text'] = detected_text
        
        # Store analysis results
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f"sessions/{session_id}/image_analysis.json",
            Body=json.dumps(analysis_results),
            ContentType='application/json'
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'analysis': analysis_results,
                'session_id': session_id
            })
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Invalid request'
            })
        }
    except Exception as e:
        logger.error(f"Image analysis failed: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Analysis failed'
            })
        }