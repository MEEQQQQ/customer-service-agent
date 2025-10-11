'use client'

import { useState } from 'react'
import { ThumbsUp, ThumbsDown, TrendingUp, Clock, CheckCircle, Zap, MessageSquare, Send, ChevronDown, ChevronUp, Code, HelpCircle, BarChart3 } from 'lucide-react'

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
    estimated_tokens: number
  }
  feedback: {
    positive: number
    negative: number
    total: number
    messages_rated: number
    comments: string[]
  }
}

export default function SessionRecap({ sessionId, onClose, onSubmitFeedback }: SessionRecapProps) {
  const [recapData, setRecapData] = useState<RecapData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showFeedbackForm, setShowFeedbackForm] = useState(false)
  const [starRating, setStarRating] = useState(5)
  const [feedbackText, setFeedbackText] = useState('')
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [advancedData, setAdvancedData] = useState<any>(null)
  const [loadingAdvanced, setLoadingAdvanced] = useState(false)

  const handleSubmitFeedback = async () => {
    setLoading(true)
    try {
      // Convert star rating to positive/negative (4-5 stars = positive, 1-3 stars = negative)
      const rating = starRating >= 4 ? 'positive' : 'negative'
      await onSubmitFeedback(rating, feedbackText)
      setFeedbackSubmitted(true)
      setShowFeedbackForm(false)
      await fetchRecap()
    } catch (err) {
      setError('Failed to submit feedback')
    } finally {
      setLoading(false)
    }
  }
  
  const handleViewMetrics = async () => {
    setShowFeedbackForm(false)
    await fetchRecap()
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
          {!recapData && (
            <div className="space-y-4 mb-6">
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Session Complete!</h3>
                <p className="text-sm text-gray-600">View your session metrics or leave optional feedback</p>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={handleViewMetrics}
                  className="flex-1 py-3 px-4 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
                >
                  <BarChart3 size={18} />
                  View Metrics
                </button>
                
                <button
                  onClick={() => setShowFeedbackForm(true)}
                  className="flex-1 py-3 px-4 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
                >
                  <MessageSquare size={18} />
                  Leave Feedback
                </button>
              </div>
            </div>
          )}
          
          {showFeedbackForm && !feedbackSubmitted && !recapData && (
            <div className="space-y-4 mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Rate Your Experience (Optional)</h3>
              
              <div className="flex justify-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setStarRating(star)}
                    className="transition-transform hover:scale-110"
                  >
                    <svg
                      className={`w-10 h-10 ${
                        star <= starRating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                      }`}
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth="1"
                    >
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                  </button>
                ))}
              </div>
              <p className="text-center text-sm text-gray-600">{starRating} out of 5 stars</p>

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
              
              <div className="flex gap-3">
                <button
                  onClick={() => setShowFeedbackForm(false)}
                  className="flex-1 py-3 px-4 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
                >
                  Skip
                </button>
                <button
                  onClick={handleSubmitFeedback}
                  disabled={loading}
                  className="flex-1 py-3 px-4 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <Send size={18} />
                  {loading ? 'Submitting...' : 'Submit Feedback'}
                </button>
              </div>
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
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 mb-4">
                <p className="text-xs text-blue-700">
                  📊 Metrics below are calculated from real CloudWatch data over the last 24 hours of system activity.
                </p>
              </div>
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
              
              <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-4 border border-purple-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MessageSquare size={18} className="text-purple-600" />
                    <span className="text-sm font-medium text-gray-700">Estimated Tokens Used</span>
                  </div>
                  <span className="text-2xl font-bold text-purple-600">{recapData.metrics.estimated_tokens}</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">Average tokens per conversation</p>
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
                  <div className="flex items-center gap-2">
                    <MessageSquare size={16} className="text-blue-600" />
                    <span className="font-medium">{recapData.feedback.messages_rated} messages rated</span>
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
                    {!advancedData && (
                      <p className="text-sm text-gray-500 text-center py-4">No advanced metrics available for this session</p>
                    )}
                    
                    {/* Lambda Metrics - Real CloudWatch Data */}
                    {advancedData?.lambda_metrics && (
                      <div>
                        <h5 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                          Lambda Metrics (Last Hour)
                          <Tooltip text="Real-time performance stats from AWS Lambda" />
                        </h5>
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          {advancedData.lambda_metrics.invocation_count !== undefined && (
                            <MetricItem label="Invocations" value={advancedData.lambda_metrics.invocation_count} tooltip="Total function calls in the last hour" />
                          )}
                          {advancedData.lambda_metrics.error_count !== undefined && (
                            <MetricItem label="Errors" value={advancedData.lambda_metrics.error_count} tooltip="Failed function executions" />
                          )}
                          {advancedData.lambda_metrics.avg_duration_ms !== undefined && (
                            <MetricItem label="Avg Duration" value={`${advancedData.lambda_metrics.avg_duration_ms}ms`} tooltip="Average execution time" />
                          )}
                          {advancedData.lambda_metrics.max_duration_ms !== undefined && (
                            <MetricItem label="Max Duration" value={`${advancedData.lambda_metrics.max_duration_ms}ms`} tooltip="Longest execution time" />
                          )}
                          {advancedData.lambda_metrics.min_duration_ms !== undefined && (
                            <MetricItem label="Min Duration" value={`${advancedData.lambda_metrics.min_duration_ms}ms`} tooltip="Fastest execution time" />
                          )}
                        </div>
                      </div>
                    )}

                    {/* API Gateway Metrics - Real CloudWatch Data */}
                    {advancedData?.api_gateway_metrics && (
                      <div>
                        <h5 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                          API Gateway Metrics (Last Hour)
                          <Tooltip text="Real-time API performance data" />
                        </h5>
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          {advancedData.api_gateway_metrics.request_count !== undefined && (
                            <MetricItem label="Total Requests" value={advancedData.api_gateway_metrics.request_count} tooltip="API calls in the last hour" />
                          )}
                          {advancedData.api_gateway_metrics.avg_latency_ms !== undefined && (
                            <MetricItem label="Avg Latency" value={`${advancedData.api_gateway_metrics.avg_latency_ms}ms`} tooltip="Average response time" />
                          )}
                          {advancedData.api_gateway_metrics.max_latency_ms !== undefined && (
                            <MetricItem label="Max Latency" value={`${advancedData.api_gateway_metrics.max_latency_ms}ms`} tooltip="Slowest response time" />
                          )}
                          {advancedData.api_gateway_metrics['4xx_errors'] !== undefined && (
                            <MetricItem label="4xx Errors" value={advancedData.api_gateway_metrics['4xx_errors']} tooltip="Client errors" />
                          )}
                          {advancedData.api_gateway_metrics['5xx_errors'] !== undefined && (
                            <MetricItem label="5xx Errors" value={advancedData.api_gateway_metrics['5xx_errors']} tooltip="Server errors" />
                          )}
                        </div>
                      </div>
                    )}

                    {/* Error Logs - Real CloudWatch Logs */}
                    {advancedData?.error_logs && advancedData.error_logs.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-gray-900 mb-2">Recent Error Logs</h5>
                        <div className="bg-red-50 rounded-lg p-3 space-y-1 max-h-48 overflow-y-auto">
                          {advancedData.error_logs.map((log: string, idx: number) => (
                            <p key={idx} className="text-xs text-red-700 font-mono break-all">{log}</p>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {advancedData && !advancedData.lambda_metrics && !advancedData.api_gateway_metrics && !advancedData.error_logs && (
                      <p className="text-sm text-gray-500 text-center py-4">No metrics data available for the last hour</p>
                    )}
                  </div>
                )}
                
                {showAdvanced && !advancedData && !loadingAdvanced && (
                  <div className="p-4 bg-white">
                    <p className="text-sm text-gray-500 text-center py-4">Unable to load advanced metrics</p>
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
