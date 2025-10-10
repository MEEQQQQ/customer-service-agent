import json
import boto3
import os
from botocore.exceptions import ClientError
import re
import uuid
from datetime import datetime

bedrock_runtime = boto3.client('bedrock-runtime')
bedrock_agent = boto3.client('bedrock-agent-runtime')
polly_client = boto3.client('polly')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET_NAME = os.environ['STORAGE_BUCKET']
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID', 'VARVMASHNX')
TICKET_TABLE_NAME = os.environ.get('TICKET_TABLE_NAME', 'ticket_log')

def lambda_handler(event, context):
    # Handle CORS preflight requests
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Max-Age': '86400',
                'Access-Control-Allow-Credentials': 'false'
            },
            'body': ''
        }
    
    try:
        body = json.loads(event['body'])
        session_id = body['session_id']
        
        # Get transcript and image analysis (if they exist)
        transcript_data = {'text': 'refer to the context provided'}
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
        
        # Generate and store ticket before troubleshooting
        ticket_id = generate_ticket(session_id, transcript_data['text'], analysis_data)
        print(f"Generated ticket: {ticket_id}")
        
        # Analyze query complexity and get knowledge base context
        query_complexity = analyze_query_complexity(transcript_data['text'])
        kb_context = get_knowledge_base_context(transcript_data['text'], analysis_data)
        
        # Call Bedrock with adaptive prompt
        try:
            prompt = build_adaptive_prompt(transcript_data['text'], analysis_data, query_complexity, kb_context, ticket_id)

            max_tokens = 512 if query_complexity == 'simple' else 1024
            native_request = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that is able to solve TV customer issues. Expected response should be concise and not ambiguous. Common issues faced are screen loading issues and overdue bills. Use Unifi TV as reference but do not mention it."},
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
        
        # Generate TTS audio with better error handling
        try:
            # Ensure text is not empty and within limits
            tts_text = agent_response.strip()
            if not tts_text:
                tts_text = "I understand your concern. Let me help you with your TV issue."
            
            # Truncate if too long (Polly limit is ~3000 chars)
            if len(tts_text) > 2500:
                tts_text = tts_text[:2500] + "..."
                print(f"WARNING: Text truncated to {len(tts_text)} characters")
            
            print(f"Generating TTS for text: {tts_text[:100]}...")
            tts_response = polly_client.synthesize_speech(
                Text=tts_text,
                OutputFormat='mp3',
                VoiceId='Aditi',
                Engine='standard'
            )
            print("TTS generation successful")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            print(f"TTS ClientError: {error_code} - {str(e)}")
            if error_code == 'TextLengthExceededException':
                tts_text = agent_response[:1500] + "..."
                print(f"Retrying with shorter text: {len(tts_text)} chars")
                tts_response = polly_client.synthesize_speech(
                    Text=tts_text,
                    OutputFormat='mp3',
                    VoiceId='Aditi',
                    Engine='standard'
                )
            else:
                raise
        except Exception as e:
            print(f"TTS generation failed: {str(e)}")
            # Generate fallback audio
            fallback_text = "I understand your concern. Let me help you with your TV issue."
            tts_response = polly_client.synthesize_speech(
                Text=fallback_text,
                OutputFormat='mp3',
                VoiceId='Aditi',
                Engine='standard'
            )
        
        # Format response for better readability
        formatted_response = format_markdown_response(agent_response)
        
        # Store audio response with proper headers
        audio_key = f"sessions/{session_id}/response.mp3"
        try:
            audio_data = tts_response['AudioStream'].read()
            print(f"Audio data size: {len(audio_data)} bytes")
            
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=audio_key,
                Body=audio_data,
                ContentType='audio/mpeg',
                CacheControl='max-age=3600',
                Metadata={
                    'Content-Type': 'audio/mpeg',
                    'session-id': session_id
                }
            )
            print(f"Audio file uploaded successfully to {audio_key}")
            
        except Exception as e:
            print(f"Failed to upload audio file: {str(e)}")
            raise
        
        # Always use presigned URL for audio playback
        try:
            audio_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': audio_key},
                ExpiresIn=3600
            )
            print(f"Generated presigned URL: {audio_url[:100]}...")
        except Exception as e:
            print(f"Failed to generate presigned URL: {str(e)}")
            audio_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{audio_key}"
        
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
                'Access-Control-Allow-Credentials': 'false',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'ticket_id': ticket_id,
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
                'Access-Control-Allow-Credentials': 'false',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }

def generate_ticket(session_id, issue_text, analysis_data):
    """Generate ticket and insert into DynamoDB"""
    ticket_id = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    timestamp = datetime.utcnow().isoformat()
    
    # Extract issue summary from text and analysis
    labels = [l['Name'] for l in analysis_data.get('labels', [])]
    extracted_text = analysis_data.get('extracted_text', [])
    issue_summary = f"{issue_text[:100]}..." if len(issue_text) > 100 else issue_text
    
    table = dynamodb.Table(TICKET_TABLE_NAME)
    table.put_item(
        Item={
            'ticket_id': ticket_id,
            'session_id': session_id,
            'issue': issue_summary,
            'full_issue': issue_text,
            'detected_labels': labels,
            'extracted_text': extracted_text,
            'timestamp': timestamp,
            'status': 'OPEN'
        }
    )
    
    return ticket_id

def generate_fallback_response(transcript, analysis):
    """Generate a basic troubleshooting response when Bedrock agent is not available"""
    detected_text = analysis.get('extracted_text', [])
    labels = [label['Name'] for label in analysis.get('labels', [])]
    
    response = "I understand you're having issues with your TV service. "
    
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



def build_adaptive_prompt(query, analysis_data, complexity, kb_context, ticket_id):
    """Build prompt based on complexity and available context"""
    base_prompt = f"""You are a TV customer service agent.

IMPORTANT: Start your response by informing the customer that their ticket {ticket_id} has been created.

Customer Issue: {query}

Image Analysis:
- Labels: {[l['Name'] for l in analysis_data.get('labels', [])]}
- Text: {analysis_data.get('extracted_text', [])}
- Custom: {[l['Name'] for l in analysis_data.get('custom_labels', [])]}

Instructions: 
1. First, acknowledge the ticket creation: "Your ticket {ticket_id} has been created."
2. Then provide the troubleshooting solution.
If the user's query is ambiguous, prompt user for asking again.
Utilize Knowledge Base context only if user's issue is clear.
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
