import pytest
import json
import base64
from unittest.mock import patch, MagicMock
import sys
import os

# Set required environment variables before importing
os.environ['STORAGE_BUCKET'] = 'test-bucket'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['TICKET_TABLE'] = 'test-ticket-table'

# Add lambda function to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda_functions', 'upload_handler'))
from upload_handler import lambda_handler

@patch('upload_handler.dynamodb')
@patch('upload_handler.s3_client')
def test_upload_handler_success(mock_s3, mock_dynamodb):
    # Mock S3 client
    mock_s3.put_object.return_value = {}
    
    # Mock DynamoDB
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.put_item.return_value = {}
    
    # Create test event
    test_image = base64.b64encode(b'fake_image_data').decode()
    test_audio = base64.b64encode(b'fake_audio_data').decode()
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'image': test_image,
            'audio': test_audio
        })
    }
    
    # Call handler
    response = lambda_handler(event, {})
    
    # Assertions
    assert response['statusCode'] == 200
    response_body = json.loads(response['body'])
    assert 'session_id' in response_body
    assert 'ticket_id' in response_body
    assert response_body['message'] == 'Files uploaded successfully'
    
    # Verify S3 calls
    assert mock_s3.put_object.call_count == 3  # image, audio, metadata
    # Verify DynamoDB call
    assert mock_table.put_item.call_count == 1

@patch('upload_handler.dynamodb')
@patch('upload_handler.s3_client')
def test_upload_handler_error(mock_s3, mock_dynamodb):
    # Mock S3 client to raise exception
    mock_s3.put_object.side_effect = Exception("S3 Error")
    
    # Mock DynamoDB
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'image': base64.b64encode(b'fake_image_data').decode()
        })
    }
    
    response = lambda_handler(event, {})
    
    assert response['statusCode'] == 500
    response_body = json.loads(response['body'])
    assert 'error' in response_body