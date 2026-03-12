import { parseCSV, stringifyCSV } from './csv'

describe('csv helpers', () => {
  test('parseCSV handles quoted commas and newlines', () => {
    const rows = parseCSV([
      'question,answer,contexts',
      '"What, exactly?","Line one',
      'Line two","[""ctx, one"", ""ctx two""]"',
    ].join('\n'))

    expect(rows).toHaveLength(1)
    expect(rows[0].question).toBe('What, exactly?')
    expect(rows[0].answer).toBe('Line one\nLine two')
    expect(rows[0].contexts).toBe('["ctx, one", "ctx two"]')
  })

  test('stringifyCSV round-trips escaped content', () => {
    const csv = stringifyCSV(
      [
        {
          question: 'What is "RAG"?',
          answer: 'Retrieval, augmented, generation',
        },
      ],
      ['question', 'answer']
    )

    expect(parseCSV(csv)).toEqual([
      {
        question: 'What is "RAG"?',
        answer: 'Retrieval, augmented, generation',
      },
    ])
  })
})