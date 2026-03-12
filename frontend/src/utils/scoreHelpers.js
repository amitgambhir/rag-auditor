export function scoreColor(score) {
  if (score === null || score === undefined) return '#6b7280'
  if (score >= 0.8) return '#22c55e'
  if (score >= 0.6) return '#f59e0b'
  return '#ef4444'
}

export function scoreLabel(score) {
  if (score === null || score === undefined) return 'N/A'
  if (score >= 0.8) return 'Excellent'
  if (score >= 0.6) return 'Fair'
  return 'Poor'
}

export function scorePct(score) {
  if (score === null || score === undefined) return 'N/A'
  return `${(score * 100).toFixed(1)}%`
}

export function hallucinationColor(risk) {
  if (risk === 'low') return '#22c55e'
  if (risk === 'medium') return '#f59e0b'
  if (risk === 'high') return '#ef4444'
  return '#6b7280'
}

export function verdictConfig(verdict) {
  switch (verdict) {
    case 'READY':
      return { label: 'PRODUCTION READY', color: '#22c55e', className: 'badge-ready' }
    case 'NEEDS_WORK':
      return { label: 'NEEDS WORK', color: '#f59e0b', className: 'badge-needs-work' }
    case 'NOT_READY':
      return { label: 'NOT READY', color: '#ef4444', className: 'badge-not-ready' }
    default:
      return { label: verdict, color: '#6b7280', className: 'badge-not-ready' }
  }
}

export function metricDescription(metric) {
  const map = {
    faithfulness: 'Is the answer grounded in the retrieved context?',
    answer_relevancy: 'Does the answer address the question?',
    context_precision: 'How relevant are the retrieved chunks (signal vs noise)?',
    context_recall: 'Was all relevant information retrieved?',
  }
  return map[metric] || metric
}

export function deltaColor(delta) {
  if (delta === null || delta === undefined) return '#6b7280'
  if (delta > 0.01) return '#22c55e'
  if (delta < -0.01) return '#ef4444'
  return '#6b7280'
}

export function deltaLabel(delta) {
  if (delta === null || delta === undefined) return '—'
  const sign = delta > 0 ? '+' : ''
  return `${sign}${(delta * 100).toFixed(1)}%`
}
