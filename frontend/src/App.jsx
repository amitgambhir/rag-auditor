import React, { useState, useCallback } from 'react'
import { Zap, BarChart2, Layers, Database, GitCompare, History as HistoryIcon } from 'lucide-react'
import { EvaluatorForm } from './components/EvaluatorForm'
import { ResultsDashboard } from './components/ResultsDashboard'
import { BatchEvaluator } from './components/BatchEvaluator'
import { DatasetGenerator } from './components/DatasetGenerator'
import { CompareMode } from './components/CompareMode'
import { HistoryPanel } from './components/HistoryPanel'
import { useEvaluate } from './hooks/useEvaluate'
import { useHistory } from './hooks/useHistory'

const TABS = [
  { id: 'evaluate', label: 'Evaluate', icon: Zap },
  { id: 'batch', label: 'Batch', icon: Layers },
  { id: 'dataset', label: 'Dataset', icon: Database },
  { id: 'compare', label: 'Compare', icon: GitCompare },
  { id: 'history', label: 'History', icon: HistoryIcon },
]

function ErrorBanner({ error, onDismiss }) {
  if (!error) return null
  return (
    <div className="mb-4 card bg-red/10 border-red/20 flex items-center justify-between gap-3">
      <p className="text-sm text-red">{error}</p>
      <button
        onClick={onDismiss}
        className="text-muted hover:text-red transition-colors text-lg leading-none"
      >
        ×
      </button>
    </div>
  )
}

export default function App() {
  const [activeTab, setActiveTab] = useState('evaluate')
  const { loading, progress, result, error, evaluate, cancel, reset } = useEvaluate()
  const { history, addEntry, clearHistory } = useHistory()

  const handleEvaluate = useCallback(
    (payload) => {
      evaluate(payload, true)
    },
    [evaluate]
  )

  const handleSave = useCallback(() => {
    if (result) {
      addEntry({
        ...result,
        question: result._question,
      })
    }
  }, [result, addEntry])

  const handleSelectHistory = useCallback(
    (entry) => {
      setActiveTab('evaluate')
    },
    []
  )

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-border sticky top-0 z-10 bg-bg/95 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-teal/10 border border-teal/20 flex items-center justify-center">
              <Zap size={16} className="text-teal" />
            </div>
            <div>
              <h1 className="text-sm font-mono font-bold text-text">RAG Auditor</h1>
              <p className="text-xs text-muted hidden sm:block">
                Know if your RAG is production-ready
              </p>
            </div>
          </div>
          <nav className="flex">
            {TABS.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 text-xs font-mono transition-colors rounded-lg ${
                    activeTab === tab.id
                      ? 'text-teal bg-teal/10'
                      : 'text-text-dim hover:text-text'
                  }`}
                >
                  <Icon size={13} />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        <ErrorBanner error={error} onDismiss={reset} />

        {activeTab === 'evaluate' && (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Form */}
            <div className="lg:col-span-2">
              <div className="card sticky top-24">
                <h2 className="text-sm font-mono font-semibold text-text-dim uppercase tracking-wider mb-4">
                  Run Evaluation
                </h2>
                <EvaluatorForm
                  onEvaluate={handleEvaluate}
                  loading={loading}
                  progress={progress}
                  onCancel={cancel}
                />
              </div>
            </div>

            {/* Results */}
            <div className="lg:col-span-3">
              {!result && !loading && (
                <div className="card flex flex-col items-center gap-4 py-16 text-center">
                  <div className="w-16 h-16 rounded-2xl bg-teal/5 border border-teal/10 flex items-center justify-center">
                    <BarChart2 size={28} className="text-teal/50" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text-dim">
                      Your results will appear here
                    </p>
                    <p className="text-xs text-muted mt-1">
                      Fill in the form and run an audit
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2 justify-center text-xs font-mono text-muted mt-2">
                    {['Faithfulness', 'Answer Relevancy', 'Context Precision', 'Context Recall', 'Hallucination Risk'].map((m) => (
                      <span key={m} className="px-2 py-1 border border-border rounded">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {result && (
                <ResultsDashboard
                  result={result}
                  onSave={handleSave}
                  onReset={reset}
                />
              )}
            </div>
          </div>
        )}

        {activeTab === 'batch' && (
          <div>
            <h2 className="text-lg font-mono font-bold text-text mb-6">Batch Evaluator</h2>
            <BatchEvaluator />
          </div>
        )}

        {activeTab === 'dataset' && (
          <div>
            <h2 className="text-lg font-mono font-bold text-text mb-2">
              Dataset Generator
            </h2>
            <p className="text-sm text-text-dim mb-6">
              Generate a synthetic golden dataset from your source documents — the fastest
              way to start evaluating your RAG system.
            </p>
            <DatasetGenerator />
          </div>
        )}

        {activeTab === 'compare' && (
          <div>
            <h2 className="text-lg font-mono font-bold text-text mb-2">Compare Mode</h2>
            <p className="text-sm text-text-dim mb-6">
              Paste two evaluation result JSONs to see metric deltas and regressions.
            </p>
            <CompareMode />
          </div>
        )}

        {activeTab === 'history' && (
          <div>
            <h2 className="text-lg font-mono font-bold text-text mb-6">Evaluation History</h2>
            <HistoryPanel
              history={history}
              onSelect={handleSelectHistory}
              onClear={clearHistory}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-16 py-6">
        <div className="max-w-6xl mx-auto px-4 flex items-center justify-between text-xs font-mono text-muted">
          <span>RAG Auditor v1.0.0 — MIT License</span>
          <span>Powered by RAGAS + Claude</span>
        </div>
      </footer>
    </div>
  )
}
