import { useState, useCallback, useRef } from 'react'
import { evaluateStream, evaluateRAG } from '../api/client'

export function useEvaluate() {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [currentRequest, setCurrentRequest] = useState(null)
  const cancelRef = useRef(null)

  const evaluate = useCallback(async (payload, useStreaming = true) => {
    setLoading(true)
    setProgress(null)
    setResult(null)
    setError(null)
    setCurrentRequest(payload)

    if (useStreaming) {
      const cancel = evaluateStream(payload, {
        onProgress: (event) => {
          setProgress(event)
        },
        onResult: (data) => {
          setResult(data)
          setLoading(false)
          setProgress(null)
        },
        onError: (err) => {
          setError(err.message)
          setLoading(false)
          setProgress(null)
        },
      })
      cancelRef.current = cancel
    } else {
      try {
        const data = await evaluateRAG(payload)
        setResult(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
        setProgress(null)
      }
    }
  }, [])

  const cancel = useCallback(() => {
    cancelRef.current?.()
    setLoading(false)
    setProgress(null)
  }, [])

  const reset = useCallback(() => {
    cancel()
    setResult(null)
    setError(null)
    setCurrentRequest(null)
  }, [cancel])

  const loadResult = useCallback((savedEntry) => {
    cancelRef.current?.()
    setLoading(false)
    setProgress(null)
    setError(null)
    setResult(savedEntry)
    setCurrentRequest(savedEntry.request || null)
  }, [])

  return {
    loading,
    progress,
    result,
    error,
    currentRequest,
    evaluate,
    cancel,
    reset,
    loadResult,
  }
}
