'use client'

import { Message } from '@/types'
import { User, Bot, Volume2 } from 'lucide-react'
import Image from 'next/image'
import ReactMarkdown from 'react-markdown'
import { useRef, useEffect, useState } from 'react'
import { ThumbsUp, ThumbsDown } from 'lucide-react'

interface ChatMessageProps {
  message: Message
  onActionClick?: (action: string) => void
  onFeedback?: (messageId: string, rating: 'positive' | 'negative') => void
}

export default function ChatMessage({ message, onActionClick, onFeedback }: ChatMessageProps) {
  const [localFeedback, setLocalFeedback] = useState<'positive' | 'negative' | null>(null)

  const handleFeedback = (rating: 'positive' | 'negative') => {
    setLocalFeedback(rating)
    onFeedback?.(message.id, rating)
  }
  const isUser = message.sender === 'user'
  const audioRef = useRef<HTMLAudioElement>(null)
  const userAudioRef = useRef<HTMLAudioElement>(null)

  // Auto-play bot audio responses
  useEffect(() => {
    if (message.audioResponse && audioRef.current && !isUser) {
      const playAudio = async () => {
        try {
          await audioRef.current?.play()
        } catch (error) {
          console.log('Auto-play failed (user interaction required):', error)
        }
      }
      playAudio()
    }
  }, [message.audioResponse, isUser])

  // // Auto-play user audio messages
  // useEffect(() => {
  //   if (message.type === 'audio' && message.audioUrl && userAudioRef.current && isUser) {
  //     const playUserAudio = async () => {
  //       try {
  //         await userAudioRef.current?.play()
  //       } catch (error) {
  //         console.log('Auto-play failed for user audio (user interaction required):', error)
  //       }
  //     }
  //     playUserAudio()
  //   }
  // }, [message.audioUrl, message.type, isUser])

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-6 message-enter message-enter-active`}>
      <div className={isUser ? 'avatar' : 'avatar-bot'}>
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>
      
      <div className={`chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-bot'}`}>
        {message.type === 'text' && (
          <div className="prose prose-sm max-w-none text-base leading-relaxed font-medium">
            <ReactMarkdown
              components={{
                p: ({children}: any) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({children}: any) => <strong className="font-bold text-gray-900">{children}</strong>,
                em: ({children}: any) => <em className="italic text-gray-800">{children}</em>,
                ul: ({children}: any) => <ul className="list-disc ml-4 mb-2">{children}</ul>,
                ol: ({children}: any) => <ol className="list-decimal ml-4 mb-2">{children}</ol>,
                li: ({children}: any) => <li className="mb-1">{children}</li>
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        
        {message.type === 'image' && message.imageUrl && (
          <div>
            <Image 
              src={message.imageUrl} 
              alt="Uploaded image" 
              width={240} 
              height={240}
              className="rounded-ios mb-3 shadow-ios-md border border-surface-200"
            />
            {message.content && <p className="text-base leading-relaxed font-medium">{message.content}</p>}
          </div>
        )}
        
        {message.type === 'audio' && message.audioUrl && (
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-primary-50 rounded-full">
              <Volume2 size={16} className="text-primary-600" />
            </div>
            <audio ref={userAudioRef} controls className="flex-1 h-8">
              <source src={message.audioUrl} type="audio/wav" />
            </audio>
          </div>
        )}
        
        {message.audioResponse && (
          <div className="mt-3 pt-3 border-t border-surface-200">
            <div className="flex items-center gap-2 mb-2">
              <Volume2 size={14} className="text-secondary-500" />
              <span className="text-sm font-medium text-text-secondary">Audio Response</span>
            </div>
            <audio 
              ref={audioRef}
              controls 
              className="w-full h-8" 
              preload="metadata"
              crossOrigin="anonymous"
            >
              <source src={message.audioResponse} type="audio/mpeg" />
              Your browser does not support the audio element.
            </audio>
          </div>
        )}
        
        {message.actions && message.actions.length > 0 && (
          <div className="mt-4 pt-3 border-t border-surface-200">
            <p className="text-sm font-medium text-text-secondary mb-2">Suggested Actions:</p>
            <div className="flex flex-wrap gap-2">
              {message.actions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => onActionClick?.(action)}
                  className="btn-secondary text-xs px-3 py-1.5 hover:bg-primary-50 hover:text-primary-700 transition-colors"
                >
                  {action}
                </button>
              ))}
            </div>
          </div>
        )}
        
        <div className="flex items-center justify-between mt-2">
          <div className={`text-xs font-medium ${isUser ? "text-white/80" : "text-text-muted" }`}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
          
          {!isUser && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleFeedback('positive')}
                className={`p-1 rounded-lg transition-all ${
                  localFeedback === 'positive'
                    ? 'bg-green-100 text-green-600'
                    : 'hover:bg-surface-100 text-text-muted hover:text-green-600'
                }`}
              >
                <ThumbsUp size={14} />
              </button>
              <button
                onClick={() => handleFeedback('negative')}
                className={`p-1 rounded-lg transition-all ${
                  localFeedback === 'negative'
                    ? 'bg-red-100 text-red-600'
                    : 'hover:bg-surface-100 text-text-muted hover:text-red-600'
                }`}
              >
                <ThumbsDown size={14} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}