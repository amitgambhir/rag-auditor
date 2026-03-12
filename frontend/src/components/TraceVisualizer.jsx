import React from 'react'
import { scoreColor, scorePct } from '../utils/scoreHelpers'
import { ArrowRight } from 'lucide-react'

const STAGES = [
  { key: 'query', label: 'Query', scoreKey: null },
  { key: 'retrieval', label: 'Retrieval', scoreKey: 'retrieval_stage' },
  { key: 'prompt', label: 'Prompt Build', scoreKey: null },
  { key: 'generation', label: 'Generation', scoreKey: 'generation_stage' },
  { key: 'answer', label: 'Answer', scoreKey: null },
]

function StageNode({ label, score, issues = [] }) {
  const color = score !== null && score !== undefined ? scoreColor(score) : '#6b7280'
  const hasScore = score !== null && score !== undefined

  return (
    <div className="flex flex-col items-center gap-2 min-w-[100px]">
      <div
        className="w-full border rounded-lg px-3 py-2.5 text-center transition-all"
        style={{
          borderColor: hasScore ? color : '#1e1e2e',
          backgroundColor: hasScore ? `${color}10` : '#12121a',
        }}
      >
        <p className="text-xs font-mono font-semibold text-text">{label}</p>
        {hasScore && (
          <p className="text-lg font-mono font-bold mt-1" style={{ color }}>
            {(score * 100).toFixed(0)}
            <span className="text-xs font-normal text-text-dim">%</span>
          </p>
        )}
      </div>
      {issues.length > 0 && (
        <div className="w-full space-y-1">
          {issues.map((issue, i) => (
            <div
              key={i}
              className="text-xs text-amber bg-amber/10 border border-amber/20 rounded px-2 py-1 leading-snug"
            >
              ⚠ {issue}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function TraceVisualizer({ trace }) {
  if (!trace) return null
  const { retrieval_stage, generation_stage } = trace

  return (
    <div className="card">
      <h3 className="text-sm font-mono font-semibold text-text-dim uppercase tracking-wider mb-4">
        RAG Pipeline Trace
      </h3>
      <div className="flex items-start gap-2 overflow-x-auto pb-2">
        {STAGES.map((stage, idx) => {
          const stageData =
            stage.scoreKey === 'retrieval_stage'
              ? retrieval_stage
              : stage.scoreKey === 'generation_stage'
              ? generation_stage
              : null

          return (
            <React.Fragment key={stage.key}>
              <div className="flex-1 min-w-[90px]">
                <StageNode
                  label={stage.label}
                  score={stageData?.score ?? null}
                  issues={stageData?.issues ?? []}
                />
              </div>
              {idx < STAGES.length - 1 && (
                <div className="flex items-start pt-3.5 text-muted flex-shrink-0">
                  <ArrowRight size={16} />
                </div>
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}
