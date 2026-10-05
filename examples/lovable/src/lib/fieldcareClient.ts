export type DiagnosisInput = {
  question: string
  equipment_id?: string
}

export type FieldCareEvent = {
  type: string
  [key: string]: unknown
}

export async function* streamDiagnosis(
  input: DiagnosisInput,
  signal?: AbortSignal,
): AsyncGenerator<FieldCareEvent> {
  const response = await fetch('/api/fieldcare', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
    signal,
  })

  if (!response.ok) {
    throw new Error(`FieldCare request failed (${response.status}).`)
  }

  const contentType = response.headers.get('content-type') ?? ''
  // Clarifications may be ordinary JSON; successful answers use newline-delimited events.
  if (contentType.includes('application/json')) {
    const result: unknown = await response.json()
    yield { type: 'response', response: result }
    return
  }

  if (!response.body) throw new Error('FieldCare returned no response stream.')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let pending = ''
  let terminal = false

  const parseLine = (line: string): FieldCareEvent | undefined => {
    const trimmed = line.trim()
    if (!trimmed) return undefined

    let value: unknown
    try {
      value = JSON.parse(trimmed)
    } catch {
      throw new Error('FieldCare returned an invalid stream event.')
    }
    if (!value || typeof value !== 'object' || !('type' in value)) {
      throw new Error('FieldCare returned an unrecognized stream event.')
    }
    return value as FieldCareEvent
  }

  try {
    while (true) {
      const { value, done } = await reader.read()
      // Network chunks can split a JSON event, so hold text until a complete line arrives.
      pending += decoder.decode(value, { stream: !done })

      let newline = pending.indexOf('\n')
      while (newline !== -1) {
        const line = pending.slice(0, newline)
        pending = pending.slice(newline + 1)
        if (line.length > 64_000) throw new Error('FieldCare stream event exceeded the size limit.')
        const event = parseLine(line)
        if (event) {
          if (event.type === 'complete' || event.type === 'error') terminal = true
          yield event
        }
        newline = pending.indexOf('\n')
      }
      if (pending.length > 64_000) throw new Error('FieldCare stream event exceeded the size limit.')

      if (done) break
    }

    const finalEvent = parseLine(pending)
    if (finalEvent) {
      if (finalEvent.type === 'complete' || finalEvent.type === 'error') terminal = true
      yield finalEvent
    }
    if (!terminal) throw new Error('FieldCare stream ended without a terminal event.')
  } finally {
    // Also close the upstream response if the UI stops consuming the async iterator early.
    await reader.cancel().catch(() => undefined)
    reader.releaseLock()
  }
}
