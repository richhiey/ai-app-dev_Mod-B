import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { streamDiagnosis } from '../lib/fieldcareClient'

export const Route = createFileRoute('/')({ component: Companion })
function Companion() {
  const [question, setQuestion] = useState('Which filter and airflow checks are documented?')
  const [equipment, setEquipment] = useState('EQ-FC-1002')
  const [answer, setAnswer] = useState('')
  const [status, setStatus] = useState('Ready to submit')
  const [requestId, setRequestId] = useState('')
  const [citations, setCitations] = useState<string[]>([])
  const [mode, setMode] = useState('No request yet')
  const [busy, setBusy] = useState(false)
  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!question.trim() || busy) return
    setBusy(true); setAnswer(''); setRequestId(''); setCitations([]); setMode('Awaiting service'); setStatus('Loading')
    try {
      for await (const event of streamDiagnosis({ question: question.trim(), ...(equipment.trim() ? { equipment_id: equipment.trim() } : {}) })) {
        if (event.type === 'metadata') {
          setRequestId(String(event.request_id ?? '')); setMode(String(event.mode ?? 'unknown'))
          setCitations(Array.isArray(event.citations) ? event.citations.map(String) : [])
        } else if (event.type === 'delta') {
          setAnswer(previous => previous + String(event.text ?? ''))
        } else if (event.type === 'complete') {
          setStatus('Complete')
        } else if (event.type === 'error') {
          throw new Error(`Service stream failed: ${String(event.category ?? 'unknown')}. Partial text is not final.`)
        } else if (event.type === 'response') {
          const value = event.response as Record<string, unknown>
          setMode(String(value.mode ?? 'unknown')); setAnswer(String(value.answer ?? ''))
          setRequestId(String(event.request_id ?? ''))
          setCitations(Array.isArray(value.citations) ? value.citations.map(String) : [])
          setStatus(value.status === 'needs_clarification' ? 'Needs clarification' : 'Response received')
        }
      }
    } catch (error) { setStatus(error instanceof Error ? error.message : 'Request failed') }
    finally { setBusy(false) }
  }
  return <main>
    <p className="eyebrow">HelioDesk · public local teaching reference</p>
    <h1>FieldCare companion</h1>
    <p>This recovery screen demonstrates the supplied connection. Keep your own Lovable screen for your project.</p>
    <p className="notice">Fixture mode sends real local HTTP requests but uses fixed text and no model. Provider mode must be configured separately.</p>
    <form onSubmit={submit}>
      <label htmlFor="question">Equipment question</label>
      <textarea id="question" required maxLength={2000} value={question} onChange={e => setQuestion(e.target.value)} />
      <label htmlFor="equipment">Equipment ID (optional)</label>
      <input id="equipment" maxLength={64} value={equipment} onChange={e => setEquipment(e.target.value)} />
      <button disabled={busy || !question.trim()}>{busy ? 'Receiving…' : 'Ask FieldCare'}</button>
    </form>
    <section aria-label="Response" aria-busy={busy}>
      <h2>Response</h2>
      <p role="status">{status}</p>
      <p><strong>Source mode:</strong> <span data-testid="mode">{mode}</span></p>
      <p className="answer">{answer || 'Your response will appear here.'}</p>
      <p><strong>Citations:</strong> {citations.join(', ') || 'None returned'}</p>
      <p><strong>Request ID:</strong> <code data-testid="request-id">{requestId || 'Not returned'}</code></p>
    </section>
  </main>
}
