import React, { useState } from 'react'
import { ArrowUp, ArrowDown, Minus, GitCompare, Loader2, AlertCircle } from 'lucide-react'
import { compareEvaluations } from '../api/client'
import { deltaColor, deltaLabel } from '../utils/scoreHelpers'

function DeltaRow({ delta }) {
  const color = deltaColor(delta.delta)
  const ArrowIcon =
    delta.direction === 'improved'
      ? ArrowUp
      : delta.direction === 'regressed'
      ? ArrowDown
      : Minus

  return (
    <div className="flex items-center justify-between py-3 border-b border-border/50 last:border-0">
      <span className="text-sm font-mono text-text-dim w-40">
        {delta.metric.replace(/_/g, ' ')}
      </span>
      <div className="flex items-center gap-6 text-sm font-mono">
        <span className="text-muted w-16 text-right">
          {delta.baseline !== null ? `${(delta.baseline * 100).toFixed(0)}%` : 'N/A'}
        </span>
        <span className="text-muted">→</span>
        <span className="text-text w-16 text-right">
          {delta.candidate !== null ? `${(delta.candidate * 100).toFixed(0)}%` : 'N/A'}
        </span>
        <div className="flex items-center gap-1 w-20 justify-end" style={{ color }}>
          <ArrowIcon size={12} />
          <span>{deltaLabel(delta.delta)}</span>
        </div>
      </div>
    </div>
  )
}

function PastePane({ label, value, onChange }) {
  return (
    <div className="flex-1">
      <label className="label">{label}</label>
      <textarea
        className="textarea-field font-mono text-xs"
        rows={10}
        placeholder='Paste evaluation result JSON here...'
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}

export function CompareMode() {
  const [baselineText, setBaselineText] = useState('')
  const [candidateText, setCandidateText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleCompare = async () => {
    setError(null)
    try {
      const baseline = JSON.parse(baselineText)
      const candidate = JSON.parse(candidateText)
      setLoading(true)
      const data = await compareEvaluations(baseline, candidate)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const directionColor = {
    improved: '#22c55e',
    regressed: '#ef4444',
    mixed: '#f59e0b',
    unchanged: '#6b7280',
  }

  return (
    <div className="space-y-5">
      <div className="flex gap-4">
        <PastePane label="Baseline (Before)" value={baselineText} onChange={setBaselineText} />
        <PastePane label="Candidate (After)" value={candidateText} onChange={setCandidateText} />
      </div>

      <button
        onClick={handleCompare}
        disabled={loading || !baselineText || !candidateText}
        className="btn-primary flex items-center gap-2"
      >
        {loading ? (
          <><Loader2 size={16} className="animate-spin" /> Comparing...</>
        ) : (
          <><GitCompare size={16} /> Compare Results</>
        )}
      </button>

      {error && (
        <div className="card bg-red/10 border-red/20 flex items-center gap-2">
          <AlertCircle size={16} className="text-red" />
          <span className="text-sm text-red">{error}</span>
        </div>
      )}

      {result && (
        <div className="card space-y-4">
          <div className="flex items-center gap-3">
            <h3 className="label mb-0">Comparison Results</h3>
            <span
              className="text-xs font-mono font-bold uppercase"
              style={{ color: directionColor[result.overall_direction] || '#6b7280' }}
            >
              {result.overall_direction}
            </span>
          </div>

          <div className="card bg-surface">
            <p className="text-sm text-text-dim leading-relaxed">{result.summary}</p>
          </div>

          <div>
            {result.deltas?.map((delta, i) => (
              <DeltaRow key={i} delta={delta} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
