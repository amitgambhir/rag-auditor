import React from 'react'
import { AlertTriangle, AlertCircle, Info, Wrench } from 'lucide-react'

const severityConfig = {
  critical: {
    icon: AlertTriangle,
    color: 'text-red',
    bg: 'bg-red/10',
    border: 'border-red/20',
    label: 'Critical',
  },
  warning: {
    icon: AlertCircle,
    color: 'text-amber',
    bg: 'bg-amber/10',
    border: 'border-amber/20',
    label: 'Warning',
  },
  info: {
    icon: Info,
    color: 'text-teal',
    bg: 'bg-teal/10',
    border: 'border-teal/20',
    label: 'Info',
  },
}

function RecommendationItem({ rec }) {
  const cfg = severityConfig[rec.severity] || severityConfig.info
  const Icon = cfg.icon

  return (
    <div className={`border ${cfg.border} rounded-lg p-4 ${cfg.bg}`}>
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 ${cfg.color}`}>
          <Icon size={16} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1.5">
            <span className={`text-xs font-mono font-bold uppercase tracking-wider ${cfg.color}`}>
              {cfg.label}
            </span>
            <span className="text-xs font-mono text-text-dim">
              {rec.dimension.replace(/_/g, '_')}
            </span>
            {rec.score !== null && rec.score !== undefined && (
              <span className="text-xs font-mono text-muted">
                {(rec.score * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <p className="text-sm text-text mb-2">{rec.issue}</p>
          <div className="flex items-start gap-2">
            <Wrench size={13} className="text-teal mt-0.5 flex-shrink-0" />
            <p className="text-xs text-text-dim leading-relaxed">{rec.fix}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export function RecommendationsPanel({ recommendations }) {
  if (!recommendations?.length) return null

  return (
    <div className="card">
      <h3 className="text-sm font-mono font-semibold text-text-dim uppercase tracking-wider mb-4">
        Recommendations ({recommendations.length})
      </h3>
      <div className="space-y-3">
        {recommendations.map((rec, i) => (
          <RecommendationItem key={i} rec={rec} />
        ))}
      </div>
    </div>
  )
}
