import Papa from 'papaparse'

export function parseCSV(text) {
  const source = text.trim()
  if (!source) {
    throw new Error('CSV must have header and at least one row')
  }

  const { data, errors, meta } = Papa.parse(source, {
    header: true,
    skipEmptyLines: true,
  })

  if (errors.length > 0) {
    throw new Error(`Invalid CSV: ${errors[0].message}`)
  }

  if (!meta.fields?.length || data.length === 0) {
    throw new Error('CSV must have header and at least one row')
  }

  return data
}

export function stringifyCSV(rows, fields) {
  return Papa.unparse(
    {
      fields,
      data: rows,
    },
    {
      newline: '\n',
    }
  )
}