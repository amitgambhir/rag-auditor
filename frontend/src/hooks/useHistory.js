import { useState, useCallback } from 'react'

const MAX_HISTORY = 50

export function useHistory() {
  const [history, setHistory] = useState([])

  const addEntry = useCallback((entry) => {
    setHistory((prev) => [
      { ...entry, id: Date.now(), timestamp: new Date().toISOString() },
      ...prev.slice(0, MAX_HISTORY - 1),
    ])
  }, [])

  const clearHistory = useCallback(() => setHistory([]), [])

  const getEntry = useCallback(
    (id) => history.find((h) => h.id === id),
    [history]
  )

  return { history, addEntry, clearHistory, getEntry }
}
