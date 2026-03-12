import React from 'react'
import { History, Trash2, ChevronRight } from 'lucide-react'
import { verdictConfig, scoreColor } from '../utils/scoreHelpers'

export function HistoryPanel({ history, onSelect, onClear }) {
  if (!history?.length) {
    return (
      <div className="card flex flex-col items-center gap-3 py-10 text-center">
        <History size={32} className="text-muted" />
        <p className="text-sm text-text-dim">No evaluations yet</p>
        <p className="text-xs text-muted">Run an evaluation to see history here</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-mono text-text-dim">{history.length} evaluation(s)</p>
        <button
          onClick={onClear}
          className="text-xs font-mono text-muted hover:text-red transition-colors flex items-center gap-1"
        >
          <Trash2 size={12} /> Clear
        </button>
      </div>

      <div className="space-y-2">
        {history.map((entry) => {
          const vc = verdictConfig(entry.verdict)
          return (
            <button
              key={entry.id}
              onClick={() => onSelect(entry)}
              className="card w-full text-left hover:border-teal/30 transition-all group"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-mono font-semibold ${vc.className}`}>
                      {vc.label}
                    </span>
                    <span
                      className="text-sm font-mono font-bold"
                      style={{ color: scoreColor(entry.overall_score) }}
                    >
                      {entry.overall_score !== undefined
                        ? `${(entry.overall_score * 100).toFixed(0)}%`
                        : '—'}
                    </span>
                  </div>
                  <p className="text-xs text-text-dim truncate">{entry.question || 'No question'}</p>
                  <p className="text-xs text-muted mt-0.5">
                    {entry.timestamp
                      ? new Date(entry.timestamp).toLocaleString()
                      : ''}
                  </p>
                </div>
                <ChevronRight
                  size={14}
                  className="text-muted group-hover:text-teal transition-colors flex-shrink-0"
                />
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
