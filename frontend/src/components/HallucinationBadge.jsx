import React from 'react'
import { AlertTriangle, CheckCircle, AlertCircle, HelpCircle } from 'lucide-react'
import { hallucinationColor } from '../utils/scoreHelpers'

const config = {
  low: {
    icon: CheckCircle,
    label: 'LOW RISK',
    description: 'Answer is well-grounded in provided context',
    bg: 'bg-green/10',
    border: 'border-green/20',
    text: 'text-green',
  },
  medium: {
    icon: AlertCircle,
    label: 'MEDIUM RISK',
    description: 'Some claims may lack direct context support',
    bg: 'bg-amber/10',
    border: 'border-amber/20',
    text: 'text-amber',
  },
  high: {
    icon: AlertTriangle,
    label: 'HIGH RISK',
    description: 'Significant hallucination or unsupported claims detected',
    bg: 'bg-red/10',
    border: 'border-red/20',
    text: 'text-red',
  },
}

export function HallucinationBadge({ risk }) {
  const cfg = config[risk] || {
    icon: HelpCircle,
    label: 'UNKNOWN',
    description: 'Could not assess hallucination risk',
    bg: 'bg-muted/10',
    border: 'border-muted/20',
    text: 'text-muted',
  }
  const Icon = cfg.icon

  return (
    <div className={`card flex items-center gap-4 ${cfg.bg} border ${cfg.border}`}>
      <div className={`p-2 rounded-lg ${cfg.bg} border ${cfg.border}`}>
        <Icon size={20} className={cfg.text} />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-text-dim uppercase tracking-wider">
            Hallucination Risk
          </span>
          <span className={`text-xs font-mono font-bold ${cfg.text}`}>{cfg.label}</span>
        </div>
        <p className="text-xs text-text-dim mt-0.5">{cfg.description}</p>
      </div>
    </div>
  )
}
