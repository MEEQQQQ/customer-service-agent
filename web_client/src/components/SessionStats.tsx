'use client'

import { SessionStats as SessionStatsType } from '@/lib/api'
import { Clock, MessageSquare, ThumbsUp, ThumbsDown, TrendingUp } from 'lucide-react'

interface SessionStatsProps {
  stats: SessionStatsType
  onClose: () => void
}

export default function SessionStats({ stats, onClose }: SessionStatsProps) {
  const satisfactionRate = stats.total_messages > 0
    ? ((stats.positive_feedback / (stats.positive_feedback + stats.negative_feedback)) * 100).toFixed(1)
    : '0'

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-surface rounded-ios-lg shadow-ios-lg max-w-md w-full p-6 animate-scale-in">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-text-primary">Session Summary</h2>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-text-primary transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div className="bg-primary-50 rounded-ios p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
              <MessageSquare className="text-primary-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-text-secondary">Total Messages</p>
              <p className="text-2xl font-bold text-text-primary">{stats.total_messages}</p>
            </div>
          </div>

          <div className="bg-secondary-50 rounded-ios p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-secondary-100 rounded-full flex items-center justify-center">
              <Clock className="text-secondary-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-text-secondary">Session Duration</p>
              <p className="text-2xl font-bold text-text-primary">{formatDuration(stats.session_duration)}</p>
            </div>
          </div>

          <div className="bg-accent-50 rounded-ios p-4 flex items-center gap-4">
            <div className="w-12 h-12 bg-accent-100 rounded-full flex items-center justify-center">
              <TrendingUp className="text-accent-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-text-secondary">Avg Response Time</p>
              <p className="text-2xl font-bold text-text-primary">{stats.response_time_avg.toFixed(2)}s</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-50 rounded-ios p-4">
              <div className="flex items-center gap-2 mb-2">
                <ThumbsUp className="text-green-600" size={16} />
                <p className="text-sm text-text-secondary">Positive</p>
              </div>
              <p className="text-xl font-bold text-green-600">{stats.positive_feedback}</p>
            </div>

            <div className="bg-red-50 rounded-ios p-4">
              <div className="flex items-center gap-2 mb-2">
                <ThumbsDown className="text-red-600" size={16} />
                <p className="text-sm text-text-secondary">Negative</p>
              </div>
              <p className="text-xl font-bold text-red-600">{stats.negative_feedback}</p>
            </div>
          </div>

          <div className="bg-gradient-to-r from-primary-500 to-secondary-500 rounded-ios p-4 text-white">
            <p className="text-sm opacity-90 mb-1">Satisfaction Rate</p>
            <p className="text-3xl font-bold">{satisfactionRate}%</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="btn-primary w-full mt-6"
        >
          Close
        </button>
      </div>
    </div>
  )
}