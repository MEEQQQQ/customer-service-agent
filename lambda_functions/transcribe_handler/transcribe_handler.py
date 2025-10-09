import json
import boto3
import os
import time

transcribe_client = boto3.client('transcribe')
s3_client = boto3.client('s3')
BUCKET_NAME = os.environ['STORAGE_BUCKET']

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        session_id = body['session_id']
        
        # Start transcription job
        job_name = f"transcribe-{session_id}"
        audio_uri = f"s3://{BUCKET_NAME}/sessions/{session_id}/audio.wav"
        
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': audio_uri},
            MediaFormat='wav',
            LanguageCode='en-US'
        )
        
        # Poll for completion (simplified for demo)
        max_attempts = 30
        for attempt in range(max_attempts):
            response = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                
                # Get transcript content
                import urllib.request
                with urllib.request.urlopen(transcript_uri) as response:
                    transcript_data = json.loads(response.read())
                
                transcript_text = transcript_data['results']['transcripts'][0]['transcript']
                
                # Store transcript
                s3_client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=f"sessions/{session_id}/transcript.json",
                    Body=json.dumps({
                        'text': transcript_text,
                        'confidence': transcript_data['results']['transcripts'][0].get('confidence', 0.9)
                    }),
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
                        'transcript': transcript_text,
                        'session_id': session_id
                    })
                }
                
            elif status == 'FAILED':
                raise Exception("Transcription job failed")
            
            time.sleep(2)
        
        raise Exception("Transcription job timed out")
        
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