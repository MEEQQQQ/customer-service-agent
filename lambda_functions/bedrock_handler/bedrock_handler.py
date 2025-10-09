import json
import boto3
import os
from botocore.exceptions import ClientError
import re

bedrock_runtime = boto3.client('bedrock-runtime')
bedrock_agent = boto3.client('bedrock-agent-runtime')
polly_client = boto3.client('polly')
s3_client = boto3.client('s3')
BUCKET_NAME = os.environ['STORAGE_BUCKET']
KNOWLEDGE_BASE_ID = "HU9V8VBZBI"

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        session_id = body['session_id']
        
        # Get transcript and image analysis (if they exist)
        transcript_data = {'text': 'No audio provided'}
        analysis_data = {'labels': [], 'extracted_text': [], 'custom_labels': []}
        
        try:
            transcript_obj = s3_client.get_object(
                Bucket=BUCKET_NAME,
                Key=f"sessions/{session_id}/transcript.json"
            )
            transcript_data = json.loads(transcript_obj['Body'].read())
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchKey':
                raise
            print(f"No transcript found for session {session_id}")
        
        try:
            analysis_obj = s3_client.get_object(
                Bucket=BUCKET_NAME,
                Key=f"sessions/{session_id}/image_analysis.json"
            )
            analysis_data = json.loads(analysis_obj['Body'].read())
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchKey':
                raise
            print(f"No image analysis found for session {session_id}")
        
        # Analyze query complexity and get knowledge base context
        query_complexity = analyze_query_complexity(transcript_data['text'])
        kb_context = get_knowledge_base_context(transcript_data['text'], analysis_data)
        
        # Call Bedrock with adaptive prompt
        try:
            prompt = build_adaptive_prompt(transcript_data['text'], analysis_data, query_complexity, kb_context)

            max_tokens = 512 if query_complexity == 'simple' else 1024
            native_request = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "max_completion_tokens": max_tokens,
                "temperature": 0.2,
            }

            request = json.dumps(native_request)

            try:
                model_id = "openai.gpt-oss-120b-1:0"
                response = bedrock_runtime.invoke_model(modelId=model_id, body=request)
            except Exception as e:
                print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
                exit(1)

            model_response = json.loads(response["body"].read())

            # ✅ Extract only the model-generated text
            agent_response = model_response["choices"][0]["message"]["content"]
            agent_response = re.sub(r"<reasoning>.*?</reasoning>", "", agent_response, flags=re.DOTALL).strip()

            
        except Exception as e:
            print(f"Bedrock Llama call failed: {e}")
            agent_response = generate_fallback_response(transcript_data['text'], analysis_data)
        
        # Generate TTS audio
        try:
            tts_response = polly_client.synthesize_speech(
                Text=agent_response,
                OutputFormat='mp3',
                VoiceId='Joanna'
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'TextLengthExceededException':
                truncated_text = agent_response[:2500]
                print(f"WARNING: Text length exceeded, retrying with truncated text ({len(truncated_text)} chars)")
                tts_response = polly_client.synthesize_speech(
                    Text=truncated_text,
                    OutputFormat='mp3',
                    VoiceId='Joanna'
                )
            else:
                raise
        
        # Format response for better readability
        formatted_response = format_markdown_response(agent_response)
        
        # Store audio response with proper headers
        audio_key = f"sessions/{session_id}/response.mp3"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=audio_key,
            Body=tts_response['AudioStream'].read(),
            ContentType='audio/mpeg',
            CacheControl='max-age=3600',
            Metadata={
                'Content-Type': 'audio/mpeg'
            }
        )
        
        # Use environment variable for API URL (will be set after deployment)
        api_base_url = os.environ.get('API_BASE_URL')
        if api_base_url:
            audio_url = f"{api_base_url}/audio/{session_id}"
        else:
            # Fallback to presigned URL if API URL not available
            audio_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': audio_key},
                ExpiresIn=3600
            )
        
        # Store troubleshooting response
        troubleshooting_data = {
            'response_text': formatted_response,
            'audio_key': audio_key,
            'recommended_actions': extract_actions(agent_response)
        }
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f"sessions/{session_id}/troubleshooting.json",
            Body=json.dumps(troubleshooting_data),
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
                'response': formatted_response,
                'audio_url': audio_url,
                'actions': troubleshooting_data['recommended_actions'],
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

def generate_fallback_response(transcript, analysis):
    """Generate a basic troubleshooting response when Bedrock agent is not available"""
    detected_text = analysis.get('extracted_text', [])
    labels = [label['Name'] for label in analysis.get('labels', [])]
    
    response = "I understand you're having issues with your Unifi TV service. "
    
    if 'no service' in transcript.lower() or any('no service' in text.lower() for text in detected_text):
        response += "I can see there's a 'No Service' error. Let me help you with these steps: "
        response += "1. Check if all cables are properly connected. "
        response += "2. Restart your set-top box by unplugging it for 30 seconds. "
        response += "3. I'll also check your subscription status and re-provision your service if needed."
    elif 'hdmi' in transcript.lower():
        response += "I notice you mentioned HDMI. Please ensure the HDMI cable is securely connected to both your set-top box and TV."
    else:
        response += "Let me run some diagnostics and provide you with the appropriate troubleshooting steps."
    
    return response

def analyze_query_complexity(query_text):
    """Analyze query complexity to determine response type"""
    complexity_indicators = {
        'simple': ['restart', 'reboot', 'turn on', 'turn off', 'no signal', 'black screen'],
        'complex': ['intermittent', 'sometimes', 'multiple', 'various', 'different channels', 'specific times']
    }
    
    query_lower = query_text.lower()
    word_count = len(query_text.split())
    
    if word_count > 20 or any(indicator in query_lower for indicator in complexity_indicators['complex']):
        return 'complex'
    return 'simple'

def get_knowledge_base_context(query, analysis_data):
    """Retrieve relevant context using Bedrock Knowledge Base semantic search"""
    try:
        final_query = query + " " + " ".join([l['Name'] for l in analysis_data.get('labels', [])])
        response = bedrock_agent.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 3
                }
            }
        )
        
        context = ""
        for result in response['retrievalResults']:
            context += result['content']['text'] + "\n"
        
        return context.strip()
    except Exception as e:
        print(f"KB retrieval failed: {e}")
        return ""



def build_adaptive_prompt(query, analysis_data, complexity, kb_context):
    """Build prompt based on complexity and available context"""
    base_prompt = f"""You are a Unifi TV customer service agent.

Customer Issue: {query}

Image Analysis:
- Labels: {[l['Name'] for l in analysis_data.get('labels', [])]}
- Text: {analysis_data.get('extracted_text', [])}
- Custom: {[l['Name'] for l in analysis_data.get('custom_labels', [])]}

Instructions: 
If the user's query is ambiguous, prompt user for asking again.
Utilize Knowledge Base context only if user's issue is clear..
"""
    
    if kb_context:
        base_prompt += f"\n\nKnowledge Base Context:\n{kb_context}"
    
    if complexity == 'simple':
        base_prompt += "\n\nProvide a concise, direct solution with 2-3 key steps."
    else:
        base_prompt += "\n\nProvide detailed troubleshooting with explanations, multiple options, and preventive measures."
    
    return base_prompt

def format_markdown_response(text):
    """Format response text for better markdown readability"""
    # Clean up the text
    text = text.strip()
    
    # Add proper spacing around numbered lists
    text = re.sub(r'(\d+\.)\s*', r'\n\1 ', text)
    
    # Add proper spacing around bullet points
    text = re.sub(r'([•-])\s*', r'\n\1 ', text)
    
    # Add spacing around bold text
    text = re.sub(r'\*\*(.*?)\*\*', r'\n**\1**\n', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Ensure proper paragraph spacing
    sentences = text.split('. ')
    formatted_sentences = []
    
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if sentence:
            if i < len(sentences) - 1:
                sentence += '.'
            formatted_sentences.append(sentence)
    
    # Join with proper spacing
    result = ' '.join(formatted_sentences)
    
    # Add line breaks before questions
    result = re.sub(r'(\?\s*)([A-Z])', r'\1\n\n\2', result)
    
    return result.strip()

def extract_actions(response_text):
    """Extract actionable items from the response"""
    actions = []
    if 'restart' in response_text.lower():
        actions.append('restart_stb')
    if 'provision' in response_text.lower():
        actions.append('reprovision_service')
    if 'subscription' in response_text.lower():
        actions.append('check_subscription')
    return actions
