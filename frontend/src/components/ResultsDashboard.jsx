import React from 'react'
import { CheckCircle2, XCircle, AlertTriangle, Save, RotateCcw } from 'lucide-react'
import { scoreColor, verdictConfig } from '../utils/scoreHelpers'
import { ScoreCard } from './ScoreCard'
import { HallucinationBadge } from './HallucinationBadge'
import { TraceVisualizer } from './TraceVisualizer'
import { RecommendationsPanel } from './RecommendationsPanel'

function VerdictIcon({ verdict }) {
  if (verdict === 'READY') return <CheckCircle2 size={20} className="text-green" />
  if (verdict === 'NOT_READY') return <XCircle size={20} className="text-red" />
  return <AlertTriangle size={20} className="text-amber" />
}

export function ResultsDashboard({ result, onSave, onReset }) {
  if (!result) return null

  const { overall_score, scores, trace, recommendations, verdict, explanation } = result
  const vc = verdictConfig(verdict)
  const overallColor = scoreColor(overall_score)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="card">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div
                className="text-5xl font-mono font-bold"
                style={{ color: overallColor }}
              >
                {(overall_score * 100).toFixed(0)}
              </div>
              <div className="text-xs font-mono text-text-dim uppercase tracking-wider mt-1">
                Overall Score
              </div>
            </div>
            <div className="h-14 w-px bg-border" />
            <div>
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-mono font-semibold ${vc.className}`}>
                <VerdictIcon verdict={verdict} />
                {vc.label}
              </div>
              <p className="text-sm text-text-dim mt-2 max-w-prose leading-relaxed">
                {explanation}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {onSave && (
              <button onClick={onSave} className="btn-ghost flex items-center gap-2 text-xs">
                <Save size={14} /> Save
              </button>
            )}
            {onReset && (
              <button onClick={onReset} className="btn-ghost flex items-center gap-2 text-xs">
                <RotateCcw size={14} /> New Eval
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Hallucination Risk */}
      {scores.hallucination_risk && (
        <HallucinationBadge risk={scores.hallucination_risk} />
      )}

      {/* Metric Cards */}
      <div>
        <h3 className="label mb-3">Metric Breakdown</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <ScoreCard metric="faithfulness" score={scores.faithfulness} />
          <ScoreCard metric="answer_relevancy" score={scores.answer_relevancy} />
          <ScoreCard metric="context_precision" score={scores.context_precision} />
          <ScoreCard
            metric="context_recall"
            score={scores.context_recall}
            isNA={scores.context_recall === null || scores.context_recall === undefined}
          />
        </div>
      </div>

      {/* Trace */}
      {trace && <TraceVisualizer trace={trace} />}

      {/* Recommendations */}
      {recommendations?.length > 0 && (
        <RecommendationsPanel recommendations={recommendations} />
      )}
    </div>
  )
}
