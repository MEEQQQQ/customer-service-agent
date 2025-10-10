const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-api-gateway-url.amazonaws.com/prod'

interface ApiResponse<T> {
  data?: T
  error?: string
}

interface UploadResponse {
  session_id: string
  message: string
}

interface TroubleshootResponse {
  response: string
  audio_url?: string
  session_id: string
  actions?: string[]
}

export interface SessionStats {
  total_messages: number
  session_duration: number
  response_time_avg: number
  positive_feedback: number
  negative_feedback: number
}

export class ApiClient {
  private static async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
      })
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
      const data = await response.json()
      return { data }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  static async uploadFiles(imageFile?: File, audioBlob?: Blob, textContent?: string): Promise<ApiResponse<UploadResponse>> {
    const body: any = {}
    if (imageFile) {
      const imageBase64 = await this.fileToBase64(imageFile)
      body.image = imageBase64.split(',')[1]
    }
    if (audioBlob) {
      const audioBase64 = await this.blobToBase64(audioBlob)
      body.audio = audioBase64.split(',')[1]
    }
    if (textContent) {
      body.text = textContent
    }
    return this.makeRequest<UploadResponse>('/upload', { method: 'POST', body: JSON.stringify(body) })
  }

  static async transcribeAudio(sessionId: string): Promise<ApiResponse<{transcription: string}>> {
    return this.makeRequest('/transcribe', { method: 'POST', body: JSON.stringify({ session_id: sessionId }) })
  }

  static async analyzeImage(sessionId: string): Promise<ApiResponse<{analysis: string}>> {
    return this.makeRequest('/analyze-image', { method: 'POST', body: JSON.stringify({ session_id: sessionId }) })
  }

  static async troubleshoot(sessionId: string, text?: string | undefined): Promise<ApiResponse<TroubleshootResponse>> {
    const body: any = { session_id: sessionId }
    if (text !== undefined) {
      body.text = text
    }
    return this.makeRequest<TroubleshootResponse>('/troubleshoot', { method: 'POST', body: JSON.stringify(body) })
  }

  static async executeAction(sessionId: string, action: string): Promise<ApiResponse<{message: string}>> {
    return this.makeRequest('/execute-action', { method: 'POST', body: JSON.stringify({ session_id: sessionId, action }) })
  }

  static async submitFeedback(sessionId: string, rating: 'positive' | 'negative', feedbackText: string = '', userType: string = 'user'): Promise<ApiResponse<{message: string}>> {
    return this.makeRequest('/feedback', { method: 'POST', body: JSON.stringify({ session_id: sessionId, rating, feedback_text: feedbackText, user_type: userType }) })
  }

  private static fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = error => reject(error)
    })
  }

  private static blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(blob)
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = error => reject(error)
    })
  }
}