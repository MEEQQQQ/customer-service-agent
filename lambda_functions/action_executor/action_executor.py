import json
import boto3
import os
import time

s3_client = boto3.client('s3')
BUCKET_NAME = os.environ['STORAGE_BUCKET']

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        session_id = body['session_id']
        action = body['action']
        
        # Execute the requested action
        result = execute_action(action, session_id)
        
        # Log the action execution
        action_log = {
            'session_id': session_id,
            'action': action,
            'result': result,
            'timestamp': time.time(),
            'status': 'completed' if result['success'] else 'failed'
        }
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f"sessions/{session_id}/actions/{action}_{int(time.time())}.json",
            Body=json.dumps(action_log),
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
                'action': action,
                'result': result,
                'session_id': session_id
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }

def execute_action(action, session_id):
    """Execute the specified action"""
    
    if action == 'restart_stb':
        return restart_set_top_box(session_id)
    elif action == 'reprovision_service':
        return reprovision_service(session_id)
    elif action == 'check_subscription':
        return check_subscription_status(session_id)
    else:
        return {
            'success': False,
            'message': f'Unknown action: {action}'
        }

def restart_set_top_box(session_id):
    """Simulate restarting a set-top box"""
    # In a real implementation, this would call the actual provisioning API
    print(f"Restarting STB for session {session_id}")
    
    return {
        'success': True,
        'message': 'Set-top box restart command sent successfully',
        'details': {
            'action_type': 'device_restart',
            'estimated_completion': '2-3 minutes'
        }
    }

def reprovision_service(session_id):
    """Simulate reprovisioning Unifi TV service"""
    # In a real implementation, this would call the actual provisioning API
    print(f"Reprovisioning service for session {session_id}")
    
    return {
        'success': True,
        'message': 'Service reprovisioning initiated successfully',
        'details': {
            'action_type': 'service_reprovision',
            'estimated_completion': '5-10 minutes'
        }
    }

def check_subscription_status(session_id):
    """Simulate checking subscription status"""
    # In a real implementation, this would call the actual billing/subscription API
    print(f"Checking subscription status for session {session_id}")
    
    # Simulate subscription check result
    return {
        'success': True,
        'message': 'Subscription status checked successfully',
        'details': {
            'action_type': 'subscription_check',
            'status': 'active',
            'expiry_date': '2024-12-31',
            'package': 'Unifi TV Ultimate'
        }
    }