import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail || err.response?.data?.error || err.message
    return Promise.reject(new Error(detail))
  }
)

export async function evaluateRAG(payload) {
  const { data } = await api.post('/evaluate', payload)
  return data
}

export async function evaluateBatch(samples) {
  const { data } = await api.post('/evaluate/batch', { samples })
  return data
}

export async function compareEvaluations(baseline, candidate) {
  const { data } = await api.post('/evaluate/compare', { baseline, candidate })
  return data
}

export async function generateDataset(documents, numQuestions) {
  const { data } = await api.post('/generate-dataset', {
    documents,
    num_questions: numQuestions,
  })
  return data
}

/**
 * SSE streaming evaluation.
 * Calls onProgress(event) for each SSE event, onResult(result) when complete.
 */
export function evaluateStream(payload, { onProgress, onResult, onError }) {
  const controller = new AbortController()
  const url = `${API_BASE}/evaluate/stream`
  const streamTimeoutMs = 120000
  let timedOut = false
  const timerId = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, streamTimeoutMs)

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            if (data === '[DONE]') return
            try {
              const parsed = JSON.parse(data)
              if (parsed.type === 'result') {
                onResult?.(parsed.data)
              } else if (parsed.type === 'error') {
                onError?.(new Error(parsed.message || 'Evaluation failed'))
                controller.abort()
                return
              } else {
                onProgress?.(parsed)
              }
            } catch {
              // ignore parse errors
            }
          }
        }
      }
    })
    .catch((err) => {
      if (timedOut) {
        onError?.(new Error('Evaluation timed out. Please retry, reduce input size, or check backend provider status.'))
        return
      }
      if (err.name !== 'AbortError') {
        onError?.(err)
      }
    })
    .finally(() => {
      clearTimeout(timerId)
    })

  return () => {
    clearTimeout(timerId)
    controller.abort()
  }
}
