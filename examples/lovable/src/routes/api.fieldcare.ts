import { createFileRoute } from '@tanstack/react-router'

const localServiceUrl = (): URL | null => {
  // This teaching route is intentionally restricted to a service on this computer.
  const value = process.env.FIELDCARE_SERVICE_URL ?? 'http://127.0.0.1:8000'

  try {
    const url = new URL(value)
    const isLocalHost = ['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)
    if (url.protocol !== 'http:' || !isLocalHost) return null
    return url
  } catch {
    return null
  }
}

export const Route = createFileRoute('/api/fieldcare')({
  server: {
    handlers: {
      POST: async ({ request }) => {
        // Avoid letting another website use this local UI server as a credentialed bridge.
        const origin = request.headers.get('origin')
        if (!origin || origin !== new URL(request.url).origin) {
          return Response.json({ detail: 'Requests must come from this local UI.' }, { status: 403 })
        }

        const baseUrl = localServiceUrl()
        // Read the caller key only in this server handler, never in browser code.
        const callerKey = process.env.FIELDCARE_CALLER_KEY

        if (!baseUrl || !callerKey) {
          return Response.json(
            { detail: 'Configure the local FieldCare URL and caller key in .env.local.' },
            { status: 503 },
          )
        }

        if (!request.headers.get('content-type')?.includes('application/json')) {
          return Response.json({ detail: 'Send a JSON request body.' }, { status: 415 })
        }

        let body: unknown
        try {
          body = await request.json()
        } catch {
          return Response.json({ detail: 'The request body is not valid JSON.' }, { status: 400 })
        }

        try {
          // Keep the upstream path fixed so the browser cannot choose another URL or route.
          const upstream = await fetch(new URL('/v1/diagnose-stream', baseUrl), {
            method: 'POST',
            signal: request.signal,
            headers: {
              'Content-Type': 'application/json',
              Accept: 'application/x-ndjson, application/json',
              'X-API-Key': callerKey,
            },
            body: JSON.stringify(body),
          })

          const headers = new Headers()
          for (const name of ['content-type', 'cache-control', 'x-request-id', 'retry-after']) {
            const value = upstream.headers.get(name)
            if (value) headers.set(name, value)
          }
          headers.set('Cache-Control', 'no-store')
          // Return the upstream body directly so NDJSON events arrive as a stream.
          return new Response(upstream.body, {
            status: upstream.status,
            headers,
          })
        } catch {
          return Response.json(
            { detail: 'FieldCare is not reachable. Check that its local server is running.' },
            { status: 502 },
          )
        }
      },
    },
  },
})
