#!/usr/bin/env python3
import boto3
import sys

rekognition = boto3.client('rekognition', region_name='us-east-1')

# Your TV error detection model ARN
MODEL_ARN = "arn:aws:rekognition:us-east-1:190403256083:project/tv-error-detection/version/v1/1760113338518"

def start_model(min_inference_units=1):
    """Start the Rekognition custom model"""
    try:
        print(f"Starting model: {MODEL_ARN}")
        print(f"Minimum inference units: {min_inference_units}")
        
        response = rekognition.start_project_version(
            ProjectVersionArn=MODEL_ARN,
            MinInferenceUnits=min_inference_units
        )
        
        print(f"✅ Model starting... Status: {response['Status']}")
        print("⏳ This may take a few minutes. The model needs to be in RUNNING state before use.")
        print("\nTo check status, run:")
        print(f"  python check_rekognition_status.py")
        
        return response
        
    except rekognition.exceptions.ResourceInUseException:
        print("⚠️  Model is already starting or running")
        return None
    except Exception as e:
        print(f"❌ Error starting model: {e}")
        sys.exit(1)

def check_status():
    """Check the current status of the model"""
    try:
        response = rekognition.describe_project_versions(
            ProjectArn="arn:aws:rekognition:us-east-1:190403256083:project/tv-error-detection",
            VersionNames=["v1"]
        )
        
        if response['ProjectVersionDescriptions']:
            status = response['ProjectVersionDescriptions'][0]['Status']
            print(f"Current model status: {status}")
            
            if status == 'RUNNING':
                print("✅ Model is RUNNING and ready to use!")
            elif status == 'STARTING':
                print("⏳ Model is STARTING... please wait")
            elif status == 'STOPPED':
                print("⚠️  Model is STOPPED. Run this script to start it.")
            else:
                print(f"ℹ️  Model status: {status}")
                
            return status
        else:
            print("❌ Model version not found")
            return None
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("Rekognition Custom Model Manager")
    print("=" * 60)
    
    # Check current status
    print("\n1. Checking current status...")
    status = check_status()
    
    # Start if stopped
    if status == 'STOPPED':
        print("\n2. Starting the model...")
        start_model(min_inference_units=1)
    elif status == 'RUNNING':
        print("\n✅ Model is already running. No action needed.")
    elif status == 'STARTING':
        print("\n⏳ Model is already starting. Please wait...")
    
    print("\n" + "=" * 60)
