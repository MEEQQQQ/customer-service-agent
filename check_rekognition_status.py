#!/usr/bin/env python3
import boto3

rekognition = boto3.client('rekognition', region_name='us-east-1')

MODEL_ARN = "arn:aws:rekognition:us-east-1:190403256083:project/tv-error-detection/version/v1/1760113338518"

try:
    response = rekognition.describe_project_versions(
        ProjectArn="arn:aws:rekognition:us-east-1:190403256083:project/tv-error-detection",
        VersionNames=["v1"]
    )
    
    if response['ProjectVersionDescriptions']:
        version = response['ProjectVersionDescriptions'][0]
        print(f"Model: {version['ProjectVersionArn']}")
        print(f"Status: {version['Status']}")
        print(f"Status Message: {version.get('StatusMessage', 'N/A')}")
        
        if version['Status'] == 'RUNNING':
            print("\n✅ Model is RUNNING - Ready to use!")
        elif version['Status'] == 'STOPPED':
            print("\n⚠️  Model is STOPPED - Run start_rekognition_model.py to start it")
        elif version['Status'] == 'STARTING':
            print("\n⏳ Model is STARTING - Please wait...")
            
except Exception as e:
    print(f"Error: {e}")
