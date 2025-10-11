'use client'

import { useState, useRef, useEffect } from 'react'
import { Message } from '@/types'
import { ApiClient } from '@/lib/api'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import SessionRecap from './SessionRecap'
import { Loader2, Tv, BarChart3 } from 'lucide-react'

export default function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m SUARA, your customer service assistant brought to you by Team Codezilla. How can I assist you today?',
      sender: 'bot',
      timestamp: new Date(),
      type: 'text'
    }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [recordedAudio, setRecordedAudio] = useState<File | null>(null)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [showRecap, setShowRecap] = useState(false)
  const [messageFeedback, setMessageFeedback] = useState<Record<string, 'positive' | 'negative'>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const [processingStep, setProcessingStep] = useState<string>('')

  const executeAction = async (action: string) => {
    if (!currentSessionId) {
      console.error('No session ID available for action execution')
      return
    }

    setIsLoading(true)
    setProcessingStep('Executing action...')

    try {
      const actionResult = await ApiClient.executeAction(currentSessionId, action)
      
      if (actionResult.error) {
        throw new Error(actionResult.error)
      }

      const actionResponse: Message = {
        id: Date.now().toString(),
        content: `Action "${action}" executed successfully. ${actionResult.data?.message || ''}`,
        sender: 'bot',
        timestamp: new Date(),
        type: 'text'
      }

      setMessages(prev => [...prev, actionResponse])
      
    } catch (error) {
      console.error('Action execution error:', error)
      
      const errorResponse: Message = {
        id: Date.now().toString(),
        content: `Failed to execute action "${action}": ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'bot',
        timestamp: new Date(),
        type: 'text'
      }
      
      setMessages(prev => [...prev, errorResponse])
    } finally {
      setIsLoading(false)
      setProcessingStep('')
    }
  }

  const processWithBackend = async (sessionId: string, hasImage: boolean, hasAudio: boolean, textContent?: string) => {
    try {
      let stepCount = 1
      const totalSteps = (hasAudio ? 1 : 0) + (hasImage ? 1 : 0) + 1

      // Step 1: Transcribe audio if present
      if (hasAudio) {
        setProcessingStep(`Step ${stepCount}/${totalSteps}: Transcribing audio...`)
        const transcribeResult = await ApiClient.transcribeAudio(sessionId)
        if (transcribeResult.error) {
          throw new Error(`Transcription failed: ${transcribeResult.error}`)
        }
        stepCount++
      }

      // Step 2: Analyze image if present
      if (hasImage) {
        setProcessingStep(`Step ${stepCount}/${totalSteps}: Analyzing image...`)
        const imageResult = await ApiClient.analyzeImage(sessionId)
        if (imageResult.error) {
          throw new Error(`Image analysis failed: ${imageResult.error}`)
        }
        stepCount++
      }

      // Step 3: Get troubleshooting response
      setProcessingStep(`Step ${stepCount}/${totalSteps}: Generating solution...`)
      const troubleshootResult = await ApiClient.troubleshoot(sessionId, textContent)
      
      if (troubleshootResult.error) {
        throw new Error(`Troubleshooting failed: ${troubleshootResult.error}`)
      }

      const response = troubleshootResult.data!
      
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        sender: 'bot',
        timestamp: new Date(),
        type: 'text',
        audioResponse: response.audio_url,
        sessionId: response.session_id,
        actions: response.actions
      }

      setMessages(prev => [...prev, botResponse])
      setProcessingStep('')
      
    } catch (error) {
      console.error('Backend processing error:', error)
      setProcessingStep('')
      
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: `I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again or contact support.`,
        sender: 'bot',
        timestamp: new Date(),
        type: 'text'
      }
      
      setMessages(prev => [...prev, errorResponse])
    }
  }

  const handleSendMessage = async (content: string, type: 'text' | 'image' | 'audio', file?: File) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
      type,
      imageUrl: file && type === 'image' ? URL.createObjectURL(file) : undefined,
      audioUrl: file && type === 'audio' ? URL.createObjectURL(file) : undefined,
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      let sessionId: string
      let needsUpload = type === 'image' || type === 'audio'
      
      // If we have existing session and it's text-only, reuse session
      if (currentSessionId && !needsUpload) {
        sessionId = currentSessionId
        setProcessingStep('Processing message...')
      } else {
        // Upload files (creates new session or uploads to existing)
        setProcessingStep(needsUpload ? 'Uploading files...' : 'Creating session...')
        const uploadResult = await ApiClient.uploadFiles(
          type === 'image' ? file : undefined,
          type === 'audio' ? file as Blob : undefined,
          type === 'text' ? content : undefined,
          currentSessionId || undefined
        )

        if (uploadResult.error) {
          throw new Error(`Upload failed: ${uploadResult.error}`)
        }

        sessionId = uploadResult.data!.session_id
        if (!currentSessionId) {
          setCurrentSessionId(sessionId)
        }
      }

      // Process with backend pipeline
      await processWithBackend(sessionId, type === 'image', type === 'audio', type === 'text' ? content : undefined)
    } catch (error) {
      console.error('Error sending message:', error)
      setProcessingStep('')
      
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        sender: 'bot',
        timestamp: new Date(),
        type: 'text'
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      setProcessingStep('')
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        const audioUrl = URL.createObjectURL(audioBlob)
        
        // Auto-send the audio message
        setTimeout(() => {
          handleSendMessage('Audio message describing the issue', 'audio', audioBlob as File)
          // Clear the recorded audio after sending to prevent it from being sent again
          setRecordedAudio(null)
        }, 100)
        
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Error starting recording:', error)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-surface shadow-ios-xl rounded-ios-lg overflow-hidden">
      {/* Header */}
      <div className="header-gradient text-white p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center shadow-ios backdrop-blur-ios">
              <Tv size={24} />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight">SUARA</h1>
              <p className="text-sm opacity-90 font-medium">AI-Powered Customer Service</p>
            </div>
          </div>
          
          {currentSessionId && (
            <button
              onClick={() => setShowRecap(true)}
              className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 backdrop-blur-ios rounded-xl transition-colors text-sm font-medium shadow-ios"
            >
              <BarChart3 size={16} />
              End Session
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 bg-background custom-scrollbar">
        <div className="space-y-4">
          {messages.map((message) => (
            <ChatMessage 
              key={message.id} 
              message={message} 
              onActionClick={executeAction}
              onFeedback={async (messageId, rating) => {
                setMessageFeedback(prev => ({ ...prev, [messageId]: rating }))
                if (currentSessionId) {
                  await ApiClient.submitFeedback(currentSessionId, rating, '', messageId)
                }
              }}
            />
          ))}
          
          {isLoading && (
            <div className="flex gap-3 mb-6 message-enter message-enter-active">
              <div className="avatar-bot">
                <Loader2 size={16} className="animate-spin text-primary-600" />
              </div>
              <div className="chat-bubble chat-bubble-bot">
                <div className="flex items-center gap-3">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm text-text-secondary font-medium">
                      {processingStep || 'Analyzing your issue...'}
                    </span>
                    {processingStep && (
                      <div className="mt-2 w-32 bg-surface-200 rounded-full h-1.5">
                        <div className="bg-primary-500 h-1.5 rounded-full animate-pulse" style={{width: '60%'}}></div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-surface-200 bg-surface/50 backdrop-blur-ios">
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isRecording={isRecording}
          recordedAudio={recordedAudio}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          onClearRecordedAudio={() => setRecordedAudio(null)}
        />
      </div>

      {/* Session Recap Modal */}
      {showRecap && currentSessionId && (
        <SessionRecap 
          sessionId={currentSessionId} 
          onClose={() => setShowRecap(false)}
          onSubmitFeedback={async (rating, feedbackText) => {
            await ApiClient.submitFeedback(currentSessionId, rating, feedbackText)
          }}
        />
      )}
    </div>
  )
}
