import { describe, it, expect } from 'vitest'
import { scoreColor, scorePct, verdictConfig, deltaLabel } from './scoreHelpers'

describe('scoreColor', () => {
  it('returns green for scores >= 0.8', () => {
    expect(scoreColor(0.9)).toBe('#22c55e')
    expect(scoreColor(0.8)).toBe('#22c55e')
  })
  it('returns amber for scores 0.6-0.8', () => {
    expect(scoreColor(0.7)).toBe('#f59e0b')
    expect(scoreColor(0.6)).toBe('#f59e0b')
  })
  it('returns red for scores < 0.6', () => {
    expect(scoreColor(0.5)).toBe('#ef4444')
    expect(scoreColor(0.0)).toBe('#ef4444')
  })
  it('returns muted for null/undefined', () => {
    expect(scoreColor(null)).toBe('#6b7280')
    expect(scoreColor(undefined)).toBe('#6b7280')
  })
})

describe('scorePct', () => {
  it('formats score as percentage', () => {
    expect(scorePct(0.75)).toBe('75.0%')
    expect(scorePct(1.0)).toBe('100.0%')
  })
  it('returns N/A for null', () => {
    expect(scorePct(null)).toBe('N/A')
  })
})

describe('verdictConfig', () => {
  it('returns correct config for READY', () => {
    const cfg = verdictConfig('READY')
    expect(cfg.color).toBe('#22c55e')
    expect(cfg.label).toBe('PRODUCTION READY')
  })
  it('returns correct config for NEEDS_WORK', () => {
    const cfg = verdictConfig('NEEDS_WORK')
    expect(cfg.color).toBe('#f59e0b')
  })
  it('returns correct config for NOT_READY', () => {
    const cfg = verdictConfig('NOT_READY')
    expect(cfg.color).toBe('#ef4444')
  })
})

describe('deltaLabel', () => {
  it('formats positive delta with +', () => {
    expect(deltaLabel(0.05)).toBe('+5.0%')
  })
  it('formats negative delta', () => {
    expect(deltaLabel(-0.03)).toBe('-3.0%')
  })
  it('returns dash for null', () => {
    expect(deltaLabel(null)).toBe('—')
  })
})
