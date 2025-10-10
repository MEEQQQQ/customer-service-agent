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
GUARDRAIL_ID = os.environ.get('GUARDRAIL_ID', '')
GUARDRAIL_VERSION = os.environ.get('GUARDRAIL_VERSION', 'DRAFT')

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
        user_text = body.get('text', '')
        
        # Get transcript and image analysis (if they exist)
        transcript_data = {'text': user_text or 'refer to the context provided'}
        analysis_data = {'labels': [], 'extracted_text': [], 'custom_labels': []}
        
        try:
            transcript_obj = s3_client.get_object(
                Bucket=BUCKET_NAME,
                Key=f"sessions/{session_id}/transcript.json"
            )
            transcript_data = json.loads(transcript_obj['Body'].read())
            # Override with new text if provided
            if user_text:
                transcript_data['text'] = user_text
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchKey':
                raise
            print(f"No transcript found for session {session_id}, using provided text")
        
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
        
        # Get or create ticket (only creates once per session)
        ticket_id = get_or_create_ticket(session_id, transcript_data['text'], analysis_data)
        print(f"Using ticket: {ticket_id}")
        
        # Load conversation history
        conversation_history = load_conversation_history(session_id)
        is_first_message = len(conversation_history) == 0
        
        # Analyze query complexity and get knowledge base context
        query_complexity = analyze_query_complexity(transcript_data['text'])
        kb_context = get_knowledge_base_context(transcript_data['text'], analysis_data)
        
        # Call Bedrock with adaptive prompt
        try:
            prompt = build_adaptive_prompt(transcript_data['text'], analysis_data, query_complexity, kb_context, ticket_id, is_first_message)
            
            # Build messages with conversation history
            messages = []
            if not conversation_history:
                messages.append({"role": "system", "content": "You are a helpful assistant that is able to solve TV customer issues. Expected response should be concise and not ambiguous. Common issues faced are screen loading issues and overdue bills. Use Unifi TV as reference but do not mention it."})
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": prompt})

            max_tokens = 512 if query_complexity == 'simple' else 1024
            native_request = {
                "messages": messages,
                "max_completion_tokens": max_tokens,
                "temperature": 0.2,
            }

            request = json.dumps(native_request)

            try:
                model_id = "openai.gpt-oss-120b-1:0"
                
                # Apply Guardrail if configured
                invoke_params = {'modelId': model_id, 'body': request}
                if GUARDRAIL_ID:
                    invoke_params['guardrailIdentifier'] = GUARDRAIL_ID
                    invoke_params['guardrailVersion'] = GUARDRAIL_VERSION
                    print(f"Using Guardrail: {GUARDRAIL_ID} v{GUARDRAIL_VERSION}")
                
                response = bedrock_runtime.invoke_model(**invoke_params)
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                
                if error_code == 'ValidationException' and 'guardrail' in str(e).lower():
                    print(f"🛡️ Guardrail blocked request: {e}")
                    # Use guardrail's configured blocked message
                    agent_response = "I'm here to provide helpful and respectful customer service. I noticed your message contains either sensitive personal information (like credit card numbers, SSN, or bank details) or inappropriate content. Please rephrase your message professionally, and I'll be happy to assist you with your TV service needs."
                else:
                    print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
                    raise
            except Exception as e:
                print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
                raise

            model_response = json.loads(response["body"].read())

            # ✅ Extract only the model-generated text
            agent_response = model_response["choices"][0]["message"]["content"]
            agent_response = re.sub(r"<reasoning>.*?</reasoning>", "", agent_response, flags=re.DOTALL).strip()
            
            # Log if Guardrail was triggered
            if 'amazon-bedrock-guardrailAction' in response.get('ResponseMetadata', {}).get('HTTPHeaders', {}):
                print(f"⚠️ Guardrail action taken: {response['ResponseMetadata']['HTTPHeaders']['amazon-bedrock-guardrailAction']}")
            
            # Save conversation to history
            save_conversation_history(session_id, prompt, agent_response)
            
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

def load_conversation_history(session_id):
    """Load conversation history from S3"""
    try:
        history_obj = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=f"sessions/{session_id}/conversation_history.json"
        )
        history = json.loads(history_obj['Body'].read())
        return history.get('messages', [])
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return []
        raise

def save_conversation_history(session_id, user_message, assistant_message):
    """Save conversation to S3"""
    history = load_conversation_history(session_id)
    
    # Add system message only on first interaction
    if not history:
        history.append({"role": "system", "content": "You are a helpful TV customer service agent. Respond naturally to each question. If the topic changes, follow the new topic. Be conversational and concise. Don't repeat ticket numbers in follow-ups."})
    
    # Extract just the user query without all the context
    clean_user_message = user_message.split('Customer Query:')[1].split('\n')[0].strip() if 'Customer Query:' in user_message else user_message
    
    history.append({"role": "user", "content": clean_user_message})
    history.append({"role": "assistant", "content": assistant_message})
    
    # Keep only last 10 exchanges (20 messages) + system message
    if len(history) > 21:
        history = [history[0]] + history[-20:]
    
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=f"sessions/{session_id}/conversation_history.json",
        Body=json.dumps({'messages': history}),
        ContentType='application/json'
    )

def get_or_create_ticket(session_id, issue_text, analysis_data):
    """Get existing ticket or create new one for session"""
    # Check if ticket already exists in session metadata
    try:
        metadata_obj = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=f"sessions/{session_id}/metadata.json"
        )
        metadata = json.loads(metadata_obj['Body'].read())
        if 'ticket_id' in metadata:
            print(f"Ticket already exists for session: {metadata['ticket_id']}")
            return metadata['ticket_id']
    except ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchKey':
            raise
        metadata = {}
    
    # Create new ticket (format: TKT202510109F18F862)
    ticket_id = f"TKT{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
    timestamp = datetime.utcnow().isoformat()
    
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
    print(f"Created new ticket: {ticket_id}")
    
    # Save ticket_id to metadata
    metadata['ticket_id'] = ticket_id
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=f"sessions/{session_id}/metadata.json",
        Body=json.dumps(metadata),
        ContentType='application/json'
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



def build_adaptive_prompt(query, analysis_data, complexity, kb_context, ticket_id, is_first_message=False):
    """Build prompt based on complexity and available context"""
    # Extract TV error detection results
    tv_errors = [l['Name'] for l in analysis_data.get('tv_error_detection', [])]
    has_visual_context = tv_errors or analysis_data.get('labels') or analysis_data.get('extracted_text')
    
    # Detect if this is an actual issue or casual chat
    query_lower = query.lower()
    issue_keywords = ['error', 'not working', 'problem', 'issue', 'broken', 'fix', 'help', 'no signal', 
                      'black screen', 'no service', 'cant', "can't", 'unable', 'failed', 'wrong']
    casual_keywords = ['hello', 'hi', 'hey', 'thanks', 'thank you', 'good', 'great', 'okay', 'ok']
    
    is_issue = any(keyword in query_lower for keyword in issue_keywords) or has_visual_context
    is_casual = any(keyword in query_lower for keyword in casual_keywords) and not is_issue
    
    # Build context-aware prompt
    if is_first_message:
        if is_casual:
            # Casual greeting - no ticket mention
            base_prompt = f"""Customer Query: {query}

Instructions:
1. Respond warmly and naturally to the greeting
2. Ask how you can help with their TV service
3. Be friendly and conversational
4. DO NOT mention ticket numbers for casual greetings"""
        else:
            # Actual issue - mention ticket
            base_prompt = f"""Customer Query: {query}

Ticket: {ticket_id}

Context:
- TV Errors: {tv_errors if tv_errors else 'None'}
- Visual Info: {[l['Name'] for l in analysis_data.get('labels', [])]}
- Screen Text: {analysis_data.get('extracted_text', [])}

Instructions:
1. This is a technical issue - mention ticket number once (e.g., "I've created ticket {ticket_id} to help you")
2. Address the specific issue mentioned
3. Provide troubleshooting steps"""
    else:
        # Follow-up message
        if is_casual:
            base_prompt = f"""Customer Query: {query}

Instructions:
1. Respond naturally to the message
2. Be conversational and friendly
3. DO NOT mention ticket numbers for casual responses"""
        elif has_visual_context:
            base_prompt = f"""Customer Query: {query}

New Context:
- TV Errors: {tv_errors if tv_errors else 'None'}
- Visual Info: {[l['Name'] for l in analysis_data.get('labels', [])]}
- Screen Text: {analysis_data.get('extracted_text', [])}

Instructions:
1. Respond naturally to the current question
2. If it's a new topic, address it directly without referring back to previous issues
3. Be conversational like a human agent"""
        else:
            base_prompt = f"""Customer Query: {query}

Instructions:
1. Respond naturally to the current question
2. If topic changed, follow the new topic
3. Be conversational and helpful"""
    
    if kb_context and is_issue:
        base_prompt += f"\n\nKnowledge: {kb_context}"
    
    if complexity == 'simple':
        base_prompt += "\n\nKeep response concise (2-3 sentences)."
    else:
        base_prompt += "\n\nProvide detailed help with clear steps."
    
    return base_prompt

def format_markdown_response(text):
    """Format response text for mobile chat display"""
    text = text.strip()
    
    # Fix broken ticket IDs (handle any format with spaces/newlines)
    text = re.sub(r'TKT\s*(\d{8})\s*([A-Z0-9]{8})', r'TKT\1\2', text)
    # Make ticket IDs bold
    text = re.sub(r'(?<!\*)\bTKT(\d{8})([A-Z0-9]{8})\b(?!\*)', r'**TKT\1\2**', text)
    
    # Split into sentences for mobile-friendly paragraphs
    sentences = re.split(r'([.!?])\s+', text)
    formatted_parts = []
    current_sentence = ''
    
    for i, part in enumerate(sentences):
        if i % 2 == 0:
            current_sentence = part
        else:
            current_sentence += part
            if current_sentence.strip():
                formatted_parts.append(current_sentence.strip())
            current_sentence = ''
    
    if current_sentence.strip():
        formatted_parts.append(current_sentence.strip())
    
    # Join with double line breaks for mobile readability
    result = '\n\n'.join(formatted_parts)
    
    # Clean up excessive newlines
    result = re.sub(r'\n{3,}', '\n\n', result)
    
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
