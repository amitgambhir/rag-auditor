import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { BatchEvaluator } from './BatchEvaluator'
import { evaluateBatch } from '../api/client'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual('../api/client')
  return {
    ...actual,
    evaluateBatch: vi.fn(),
  }
})

describe('BatchEvaluator', () => {
  test('uploads exported-style CSV and renders batch results', async () => {
    evaluateBatch.mockResolvedValue({
      aggregate: {
        faithfulness: 0.91,
        answer_relevancy: 0.87,
        context_precision: 0.82,
        context_recall: 0.8,
        overall_score: 0.86,
      },
      verdict_distribution: { READY: 1 },
      total_samples: 1,
      successful: 1,
      failed: 0,
      results: [
        {
          overall_score: 0.86,
          scores: {
            faithfulness: 0.91,
            answer_relevancy: 0.87,
            context_precision: 0.82,
            context_recall: 0.8,
            hallucination_risk: 'low',
          },
          verdict: 'READY',
        },
      ],
    })

    const csv = [
      'question,answer,contexts,ground_truth',
      '"What, exactly, is RAG?","Line one of the answer.',
      'Line two of the answer.","[""context, one"", ""context two""]","Retrieval-augmented generation"',
    ].join('\n')

    const { container } = render(<BatchEvaluator />)
    const input = container.querySelector('input[type="file"]')
    const file = new File([csv], 'batch.csv', { type: 'text/csv' })
    Object.defineProperty(file, 'text', {
      value: vi.fn().mockResolvedValue(csv),
    })

    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(evaluateBatch).toHaveBeenCalledWith([
        {
          question: 'What, exactly, is RAG?',
          answer: 'Line one of the answer.\nLine two of the answer.',
          contexts: ['context, one', 'context two'],
          ground_truth: 'Retrieval-augmented generation',
          mode: 'full',
        },
      ])
    })

    expect(await screen.findByText('Aggregate Results')).toBeInTheDocument()
    expect(screen.getByText('Per-Sample Results')).toBeInTheDocument()
    expect(screen.getByText('PRODUCTION READY')).toBeInTheDocument()
  })
})