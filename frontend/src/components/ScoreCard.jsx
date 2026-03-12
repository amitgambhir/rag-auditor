import React from 'react'
import { scoreColor, scorePct, metricDescription } from '../utils/scoreHelpers'

function CircleProgress({ score, size = 80, strokeWidth = 6 }) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const progress = score !== null && score !== undefined ? score : 0
  const offset = circumference - progress * circumference
  const color = scoreColor(score)

  return (
    <svg width={size} height={size} className="rotate-[-90deg]">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#1e1e2e"
        strokeWidth={strokeWidth}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={score !== null && score !== undefined ? offset : circumference}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.6s ease-in-out, stroke 0.3s' }}
      />
    </svg>
  )
}

export function ScoreCard({ metric, score, isNA = false }) {
  const color = scoreColor(score)
  const label = metric.replace(/_/g, ' ')
  const description = metricDescription(metric)

  return (
    <div className="card flex flex-col items-center gap-3 text-center hover:border-border/80 transition-colors">
      <div className="relative">
        <CircleProgress score={isNA ? null : score} />
        <div className="absolute inset-0 flex items-center justify-center">
          <span
            className="text-base font-mono font-semibold"
            style={{ color: isNA ? '#6b7280' : color }}
          >
            {isNA ? 'N/A' : score !== null && score !== undefined ? `${(score * 100).toFixed(0)}` : '—'}
          </span>
        </div>
      </div>
      <div>
        <p className="text-xs font-mono font-semibold uppercase tracking-wider text-text-dim">
          {label}
        </p>
        <p className="text-xs text-muted mt-1 leading-snug">{description}</p>
      </div>
      {isNA && (
        <p className="text-xs text-muted italic">Provide ground truth to enable</p>
      )}
    </div>
  )
}
