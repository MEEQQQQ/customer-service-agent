'use client'

import { useState } from 'react'
import { ThumbsUp, ThumbsDown, TrendingUp, Clock, CheckCircle, Zap, MessageSquare, Send, ChevronDown, ChevronUp, Code, HelpCircle } from 'lucide-react'

interface SessionRecapProps {
  sessionId: string
  onClose: () => void
  onSubmitFeedback: (rating: 'positive' | 'negative', feedbackText: string) => void
}

interface RecapData {
  metrics: {
    response_time: number
    success_rate: number
    model_confidence: number
    system_uptime: number
    satisfaction_rate: number
  }
  feedback: {
    positive: number
    negative: number
    total: number
    comments: string[]
  }
}

export default function SessionRecap({ sessionId, onClose, onSubmitFeedback }: SessionRecapProps) {
  const [recapData, setRecapData] = useState<RecapData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showFeedbackForm, setShowFeedbackForm] = useState(true)
  const [selectedRating, setSelectedRating] = useState<'positive' | 'negative' | null>(null)
  const [feedbackText, setFeedbackText] = useState('')
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [advancedData, setAdvancedData] = useState<any>(null)
  const [loadingAdvanced, setLoadingAdvanced] = useState(false)

  const handleSubmitFeedback = async () => {
    if (!selectedRating) return
    
    setLoading(true)
    try {
      await onSubmitFeedback(selectedRating, feedbackText)
      setFeedbackSubmitted(true)
      setShowFeedbackForm(false)
      await fetchRecap()
    } catch (err) {
      setError('Failed to submit feedback')
    } finally {
      setLoading(false)
    }
  }

  const fetchRecap = async (includeAdvanced = false) => {
    setLoading(true)
    setError(null)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || ''
      const url = includeAdvanced 
        ? `${apiUrl}/session-recap/${sessionId}?advanced=true`
        : `${apiUrl}/session-recap/${sessionId}`
      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch recap')
      const data = await response.json()
      setRecapData(data)
      if (includeAdvanced && data.advanced_metrics) {
        setAdvancedData(data.advanced_metrics)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const toggleAdvanced = async () => {
    if (!showAdvanced && !advancedData) {
      setLoadingAdvanced(true)
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || ''
        const response = await fetch(`${apiUrl}/session-recap/${sessionId}?advanced=true`)
        if (response.ok) {
          const data = await response.json()
          setAdvancedData(data.advanced_metrics)
        }
      } catch (err) {
        console.error('Failed to load advanced metrics:', err)
      } finally {
        setLoadingAdvanced(false)
      }
    }
    setShowAdvanced(!showAdvanced)
  }

  const getColor = (value: number, thresholds: { good: number; moderate: number }) => {
    if (value >= thresholds.good) return 'text-green-600 bg-green-50'
    if (value >= thresholds.moderate) return 'text-orange-600 bg-orange-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">End Session</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          <p className="text-sm text-gray-500 mt-1">Session ID: {sessionId}</p>
        </div>

        <div className="p-6">
          {showFeedbackForm && !feedbackSubmitted && (
            <div className="space-y-4 mb-6">
              <h3 className="text-lg font-semibold text-gray-900">How was your experience?</h3>
              
              <div className="flex gap-4">
                <button
                  onClick={() => setSelectedRating('positive')}
                  className={`flex-1 py-4 px-4 rounded-xl font-medium transition-all ${
                    selectedRating === 'positive'
                      ? 'bg-green-100 text-green-700 border-2 border-green-500'
                      : 'bg-gray-50 text-gray-700 border-2 border-gray-200 hover:border-green-300'
                  }`}
                >
                  <ThumbsUp size={32} className="mx-auto mb-2" />
                  Satisfied
                </button>
                
                <button
                  onClick={() => setSelectedRating('negative')}
                  className={`flex-1 py-4 px-4 rounded-xl font-medium transition-all ${
                    selectedRating === 'negative'
                      ? 'bg-red-100 text-red-700 border-2 border-red-500'
                      : 'bg-gray-50 text-gray-700 border-2 border-gray-200 hover:border-red-300'
                  }`}
                >
                  <ThumbsDown size={32} className="mx-auto mb-2" />
                  Not Satisfied
                </button>
              </div>

              <div className="relative">
                <MessageSquare size={18} className="absolute left-3 top-3 text-gray-400" />
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="Tell us about your experience (optional)"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                  rows={4}
                />
              </div>
              
              <button
                onClick={handleSubmitFeedback}
                disabled={!selectedRating || loading}
                className="w-full py-3 px-4 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Send size={18} />
                {loading ? 'Submitting...' : 'Submit & View Metrics'}
              </button>
            </div>
          )}

          {feedbackSubmitted && !recapData && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center mb-6">
              <p className="text-green-700 font-medium">Thank you for your feedback! 🎉</p>
            </div>
          )}

          {loading && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading metrics...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
              {error}
            </div>
          )}

          {recapData && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <MetricCard
                  icon={<Clock size={20} />}
                  label="Response Time"
                  value={`${recapData.metrics.response_time}s`}
                  color={getColor(recapData.metrics.response_time, { good: 0, moderate: 2 })}
                />
                <MetricCard
                  icon={<CheckCircle size={20} />}
                  label="Success Rate"
                  value={`${recapData.metrics.success_rate}%`}
                  color={getColor(recapData.metrics.success_rate, { good: 95, moderate: 85 })}
                />
                <MetricCard
                  icon={<TrendingUp size={20} />}
                  label="Model Confidence"
                  value={`${recapData.metrics.model_confidence}%`}
                  color={getColor(recapData.metrics.model_confidence, { good: 80, moderate: 60 })}
                />
                <MetricCard
                  icon={<Zap size={20} />}
                  label="System Uptime"
                  value={`${recapData.metrics.system_uptime}%`}
                  color={getColor(recapData.metrics.system_uptime, { good: 99, moderate: 95 })}
                />
              </div>

              <div className="bg-gradient-to-br from-primary-50 to-secondary-50 rounded-xl p-6 border border-primary-100">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Overall Satisfaction</h3>
                  <span className={`text-3xl font-bold ${getColor(recapData.metrics.satisfaction_rate, { good: 70, moderate: 50 })}`}>
                    {recapData.metrics.satisfaction_rate}%
                  </span>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-2">
                    <ThumbsUp size={16} className="text-green-600" />
                    <span className="font-medium">{recapData.feedback.positive} positive</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <ThumbsDown size={16} className="text-red-600" />
                    <span className="font-medium">{recapData.feedback.negative} negative</span>
                  </div>
                </div>
              </div>

              {recapData.feedback.comments.length > 0 && (
                <div className="bg-gray-50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">User Comments</h4>
                  <div className="space-y-2">
                    {recapData.feedback.comments.map((comment, idx) => (
                      <p key={idx} className="text-sm text-gray-700 italic">"{comment}"</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Stats for Nerds Section */}
              <div className="border border-gray-200 rounded-xl overflow-hidden">
                <button
                  onClick={toggleAdvanced}
                  className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between text-left"
                >
                  <div className="flex items-center gap-2">
                    <Code size={18} className="text-gray-600" />
                    <div>
                      <span className="font-semibold text-gray-900">Stats for Nerds 🤓</span>
                      <p className="text-xs text-gray-500">Peek under the hood</p>
                    </div>
                  </div>
                  {loadingAdvanced ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                  ) : (
                    showAdvanced ? <ChevronUp size={18} /> : <ChevronDown size={18} />
                  )}
                </button>

                {showAdvanced && advancedData && (
                  <div className="p-4 bg-white space-y-4">
                    {/* Lambda Metrics */}
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        Lambda Metrics
                        <Tooltip text="Performance stats from AWS Lambda functions" />
                      </h5>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <MetricItem label="p50 Duration" value={`${advancedData.lambda_metrics.p50_duration}ms`} tooltip="50% of requests complete faster than this" />
                        <MetricItem label="p90 Duration" value={`${advancedData.lambda_metrics.p90_duration}ms`} tooltip="90% of requests complete faster than this" />
                        <MetricItem label="p99 Duration" value={`${advancedData.lambda_metrics.p99_duration}ms`} tooltip="99% of requests complete faster than this" />
                        <MetricItem label="Invocations" value={advancedData.lambda_metrics.invocation_count} tooltip="Total function calls in the last hour" />
                      </div>
                    </div>

                    {/* API Gateway Metrics */}
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-2">API Gateway Metrics</h5>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <MetricItem label="API Latency" value={`${advancedData.api_gateway_metrics.latency}ms`} tooltip="Time from request to response" />
                        <MetricItem label="Integration Latency" value={`${advancedData.api_gateway_metrics.integration_latency}ms`} tooltip="Time spent in backend services" />
                      </div>
                    </div>

                    {/* Bedrock Metrics */}
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-2">Bedrock Model Metrics</h5>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <MetricItem label="Inference Latency" value={`${advancedData.bedrock_metrics.inference_latency}ms`} tooltip="Time for AI model to generate response" />
                        <MetricItem label="Request Size" value={`${advancedData.bedrock_metrics.request_size_kb}KB`} tooltip="Size of data sent to model" />
                      </div>
                    </div>

                    {/* Token Usage */}
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-2">Token Usage</h5>
                      <div className="grid grid-cols-3 gap-3 text-sm">
                        <MetricItem label="Input Tokens" value={advancedData.token_usage.input_tokens} tooltip="Tokens in your question" />
                        <MetricItem label="Output Tokens" value={advancedData.token_usage.output_tokens} tooltip="Tokens in AI response" />
                        <MetricItem label="Total" value={advancedData.token_usage.total_tokens} tooltip="Total tokens used" />
                      </div>
                    </div>

                    {/* Error Logs */}
                    {advancedData.error_logs && advancedData.error_logs.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-gray-900 mb-2">Recent Errors</h5>
                        <div className="bg-red-50 rounded-lg p-3 space-y-1">
                          {advancedData.error_logs.map((log: string, idx: number) => (
                            <p key={idx} className="text-xs text-red-700 font-mono">{log}</p>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div className={`rounded-xl p-4 ${color} border`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  )
}

function MetricItem({ label, value, tooltip }: { label: string; value: string | number; tooltip: string }) {
  return (
    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
      <span className="text-gray-600 flex items-center gap-1">
        {label}
        <Tooltip text={tooltip} />
      </span>
      <span className="font-mono font-semibold">{value}</span>
    </div>
  )
}

function Tooltip({ text }: { text: string }) {
  const [show, setShow] = useState(false)
  return (
    <div className="relative">
      <HelpCircle 
        size={12} 
        className="text-gray-400 cursor-help" 
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      />
      {show && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 bg-gray-800 text-white text-xs rounded whitespace-nowrap z-10">
          {text}
        </div>
      )}
    </div>
  )
}
