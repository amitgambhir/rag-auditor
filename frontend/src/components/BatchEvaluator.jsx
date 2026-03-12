import React, { useState } from 'react'
import { Upload, Download, Loader2, AlertCircle } from 'lucide-react'
import { evaluateBatch } from '../api/client'
import { parseCSV, stringifyCSV } from '../utils/csv'
import { scoreColor, verdictConfig } from '../utils/scoreHelpers'

function parseSamples(text, format) {
  if (format === 'json') {
    const data = JSON.parse(text)
    return Array.isArray(data) ? data : [data]
  }
  return parseCSV(text)
}

function parseContexts(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean)
  }

  if (typeof value !== 'string' || !value.trim()) {
    return []
  }

  const trimmed = value.trim()
  if (trimmed.startsWith('[')) {
    try {
      const parsed = JSON.parse(trimmed)
      if (Array.isArray(parsed)) {
        return parsed.map((item) => String(item).trim()).filter(Boolean)
      }
    } catch {
      // Fall back to legacy pipe-delimited parsing.
    }
  }

  return trimmed
    .split('|')
    .map((item) => item.trim())
    .filter(Boolean)
}

export function BatchEvaluator() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(null)
  const [uploadedSamples, setUploadedSamples] = useState([])

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError(null)
    setResults(null)

    try {
      const text = await file.text()
      const format = file.name.endsWith('.json') ? 'json' : 'csv'
      const rows = parseSamples(text, format)

      const samples = rows.map((row) => ({
        question: row.question || row.Question || '',
        answer: row.answer || row.Answer || '',
        contexts: parseContexts(row.contexts),
        ground_truth: row.ground_truth || row['Ground Truth'] || null,
        mode: 'full',
      }))

      if (!samples.length) throw new Error('No valid samples found')

      setUploadedSamples(samples)
      setLoading(true)
      setProgress({ done: 0, total: samples.length })
      const data = await evaluateBatch(samples)
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setProgress(null)
    }
  }

  const exportCSV = () => {
    if (!results?.results) return
    const fields = ['question', 'verdict', 'overall_score', 'faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 'hallucination_risk']
    const rows = results.results.map((r, i) => {
      if (!r) {
        return {
          question: uploadedSamples[i]?.question || '',
          verdict: 'error',
          overall_score: '',
          faithfulness: '',
          answer_relevancy: '',
          context_precision: '',
          context_recall: '',
          hallucination_risk: '',
        }
      }

      return {
        question: uploadedSamples[i]?.question || '',
        verdict: r.verdict,
        overall_score: r.overall_score,
        faithfulness: r.scores?.faithfulness ?? '',
        answer_relevancy: r.scores?.answer_relevancy ?? '',
        context_precision: r.scores?.context_precision ?? '',
        context_recall: r.scores?.context_recall ?? '',
        hallucination_risk: r.scores?.hallucination_risk ?? '',
      }
    })
    const csv = stringifyCSV(rows, fields)
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'rag-audit-results.csv'
    a.click()
  }

  return (
    <div className="space-y-6">
      <div className="card border-dashed">
        <label className="flex flex-col items-center gap-3 cursor-pointer py-4">
          <Upload size={24} className="text-teal" />
          <div className="text-center">
            <p className="text-sm font-semibold text-text">Upload CSV or JSON</p>
            <p className="text-xs text-text-dim mt-1">
              Required columns: question, answer, contexts (JSON array or pipe-separated), ground_truth (optional)
            </p>
          </div>
          <input
            type="file"
            accept=".csv,.json"
            onChange={handleFileUpload}
            className="hidden"
          />
          <span className="btn-primary text-sm">Choose File</span>
        </label>
      </div>

      {loading && (
        <div className="card flex items-center gap-3">
          <Loader2 size={16} className="text-teal animate-spin" />
          <span className="text-sm font-mono text-teal">Evaluating samples...</span>
        </div>
      )}

      {error && (
        <div className="card bg-red/10 border-red/20 flex items-center gap-2">
          <AlertCircle size={16} className="text-red" />
          <span className="text-sm text-red">{error}</span>
        </div>
      )}

      {results && (
        <div className="space-y-4">
          {/* Aggregate */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="label mb-0">Aggregate Results</h3>
              <button onClick={exportCSV} className="btn-ghost flex items-center gap-2 text-xs">
                <Download size={14} /> Export CSV
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(results.aggregate || {}).map(([key, val]) => (
                <div key={key} className="text-center">
                  <div
                    className="text-2xl font-mono font-bold"
                    style={{ color: val !== null ? scoreColor(val) : '#6b7280' }}
                  >
                    {val !== null ? `${(val * 100).toFixed(0)}` : 'N/A'}
                  </div>
                  <div className="text-xs font-mono text-text-dim mt-1">
                    {key.replace(/_/g, ' ')}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex gap-4 flex-wrap text-xs text-text-dim font-mono">
              <span>Total: {results.total_samples}</span>
              <span className="text-green">Success: {results.successful}</span>
              {results.failed > 0 && <span className="text-red">Failed: {results.failed}</span>}
            </div>
          </div>

          {/* Results table */}
          <div className="card overflow-x-auto">
            <h3 className="label mb-3">Per-Sample Results</h3>
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="border-b border-border text-text-dim text-left">
                  <th className="py-2 pr-4">#</th>
                  <th className="py-2 pr-4">Verdict</th>
                  <th className="py-2 pr-4">Overall</th>
                  <th className="py-2 pr-4">Faithfulness</th>
                  <th className="py-2 pr-4">Relevancy</th>
                  <th className="py-2 pr-4">Precision</th>
                  <th className="py-2 pr-4">Recall</th>
                  <th className="py-2">Hallucination</th>
                </tr>
              </thead>
              <tbody>
                {results.results?.map((r, i) => {
                  if (!r) return (
                    <tr key={i} className="border-b border-border/50">
                      <td className="py-2 pr-4 text-muted">{i + 1}</td>
                      <td colSpan={7} className="py-2 text-red">Error</td>
                    </tr>
                  )
                  const vc = verdictConfig(r.verdict)
                  return (
                    <tr key={i} className="border-b border-border/50 hover:bg-surface/50">
                      <td className="py-2 pr-4 text-muted">{i + 1}</td>
                      <td className="py-2 pr-4">
                        <span className={vc.className}>{vc.label}</span>
                      </td>
                      {[
                        r.overall_score,
                        r.scores?.faithfulness,
                        r.scores?.answer_relevancy,
                        r.scores?.context_precision,
                        r.scores?.context_recall,
                      ].map((val, j) => (
                        <td key={j} className="py-2 pr-4" style={{ color: val !== null && val !== undefined ? scoreColor(val) : '#6b7280' }}>
                          {val !== null && val !== undefined ? `${(val * 100).toFixed(0)}%` : 'N/A'}
                        </td>
                      ))}
                      <td className="py-2">
                        <span style={{ color: r.scores?.hallucination_risk === 'low' ? '#22c55e' : r.scores?.hallucination_risk === 'high' ? '#ef4444' : '#f59e0b' }}>
                          {r.scores?.hallucination_risk?.toUpperCase() || 'N/A'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
