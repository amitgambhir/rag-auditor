import React, { useState } from 'react'
import { Plus, Trash2, Sparkles, Download, Loader2, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { generateDataset } from '../api/client'

function QAPairCard({ pair, index }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono text-teal">#{index + 1}</span>
            {pair.evolution_type && (
              <span className="text-xs font-mono text-text-dim bg-border px-2 py-0.5 rounded">
                {pair.evolution_type}
              </span>
            )}
          </div>
          <p className="text-sm font-semibold text-text">{pair.question}</p>
          <p className="text-sm text-text-dim mt-1 line-clamp-2">{pair.answer}</p>
        </div>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-muted hover:text-teal transition-colors flex-shrink-0"
        >
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-border space-y-2">
          <div>
            <span className="label">Ground Truth</span>
            <p className="text-xs text-text-dim">{pair.ground_truth}</p>
          </div>
          {pair.contexts?.length > 0 && (
            <div>
              <span className="label">Contexts ({pair.contexts.length})</span>
              {pair.contexts.map((ctx, i) => (
                <div key={i} className="text-xs text-text-dim bg-bg rounded p-2 mt-1 border border-border">
                  {ctx.slice(0, 200)}{ctx.length > 200 ? '...' : ''}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function DatasetGenerator() {
  const [documents, setDocuments] = useState([''])
  const [numQuestions, setNumQuestions] = useState(5)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const addDocument = () => setDocuments((prev) => [...prev, ''])
  const removeDocument = (i) => setDocuments((prev) => prev.filter((_, idx) => idx !== i))
  const updateDocument = (i, val) =>
    setDocuments((prev) => prev.map((d, idx) => (idx === i ? val : d)))

  const handleGenerate = async () => {
    const validDocs = documents.filter((d) => d.trim())
    if (!validDocs.length) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await generateDataset(validDocs, numQuestions)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const exportJSON = () => {
    if (!result) return
    const blob = new Blob([JSON.stringify(result.pairs, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'golden-dataset.json'
    a.click()
  }

  const exportCSV = () => {
    if (!result) return
    const headers = ['question', 'answer', 'ground_truth', 'contexts', 'evolution_type']
    const rows = result.pairs.map((p) => [
      `"${p.question.replace(/"/g, '""')}"`,
      `"${p.answer.replace(/"/g, '""')}"`,
      `"${p.ground_truth.replace(/"/g, '""')}"`,
      `"${(p.contexts || []).join(' | ').replace(/"/g, '""')}"`,
      p.evolution_type || 'simple',
    ])
    const csv = [headers, ...rows].map((r) => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'golden-dataset.csv'
    a.click()
  }

  return (
    <div className="space-y-5">
      <div className="card bg-teal/5 border-teal/20">
        <p className="text-sm text-text-dim leading-relaxed">
          <span className="text-teal font-semibold">No golden dataset?</span> No problem.
          Paste your source documents below and we'll generate realistic Q&A pairs
          to use as evaluation ground truth. Uses RAGAS TestsetGenerator + Claude.
        </p>
      </div>

      {/* Documents */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="label mb-0">Source Documents</label>
          <button
            onClick={addDocument}
            className="text-xs font-mono text-teal hover:text-teal-dim flex items-center gap-1"
          >
            <Plus size={12} /> Add document
          </button>
        </div>
        <div className="space-y-2">
          {documents.map((doc, i) => (
            <div key={i} className="flex gap-2">
              <textarea
                className="textarea-field"
                rows={5}
                placeholder={`Paste document ${i + 1} here...`}
                value={doc}
                onChange={(e) => updateDocument(i, e.target.value)}
              />
              {documents.length > 1 && (
                <button
                  onClick={() => removeDocument(i)}
                  className="text-muted hover:text-red transition-colors flex-shrink-0 mt-1"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Number of questions */}
      <div>
        <label className="label">Number of Q&A Pairs</label>
        <input
          type="number"
          min={1}
          max={50}
          value={numQuestions}
          onChange={(e) => setNumQuestions(Number(e.target.value))}
          className="input-field w-32"
        />
      </div>

      <button
        onClick={handleGenerate}
        disabled={loading || !documents.some((d) => d.trim())}
        className="btn-primary flex items-center gap-2"
      >
        {loading ? (
          <><Loader2 size={16} className="animate-spin" /> Generating...</>
        ) : (
          <><Sparkles size={16} /> Generate Dataset</>
        )}
      </button>

      {error && (
        <div className="card bg-red/10 border-red/20 flex items-center gap-2">
          <AlertCircle size={16} className="text-red" />
          <span className="text-sm text-red">{error}</span>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-mono text-teal">
              Generated {result.total} Q&A pairs from {result.source_documents} document(s)
            </p>
            <div className="flex gap-2">
              <button onClick={exportJSON} className="btn-ghost flex items-center gap-2 text-xs">
                <Download size={12} /> JSON
              </button>
              <button onClick={exportCSV} className="btn-ghost flex items-center gap-2 text-xs">
                <Download size={12} /> CSV
              </button>
            </div>
          </div>
          <div className="space-y-3">
            {result.pairs.map((pair, i) => (
              <QAPairCard key={i} pair={pair} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
