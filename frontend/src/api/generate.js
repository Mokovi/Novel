/**
 * SSE generation client — uses fetch() with ReadableStream for POST + streaming.
 */

function consumeSSE(url, handlers, body, token) {
  const controller = new AbortController()

  ;(async () => {
    try {
      const headers = { 'Content-Type': 'application/json' }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const resp = await fetch(url, {
        method: 'POST',
        headers,
        body: body ? JSON.stringify(body) : '{}',
        signal: controller.signal,
      })

      if (!resp.ok) {
        const err = await resp.text().catch(() => 'Unknown error')
        handlers.onError?.(`HTTP ${resp.status}: ${err}`)
        return
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const payload = line.slice(6).trim()
          if (!payload) continue

          try {
            const evt = JSON.parse(payload)
            switch (evt.event) {
              case 'start':
                handlers.onStart?.(evt)
                break
              case 'token':
                handlers.onToken?.(evt.token)
                break
              case 'summary':
                handlers.onSummary?.(evt.summary)
                break
              case 'done':
                handlers.onDone?.(evt)
                break
              case 'error':
                handlers.onError?.(evt.message)
                break
            }
          } catch {
            // skip malformed JSON
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        handlers.onError?.(err.message || 'Connection failed')
      }
    }
  })()

  return controller
}

function getToken() {
  return localStorage.getItem('auth_token')
}

const BASE = '/api/v1'

export function generateChapter(chapterId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/generate/chapter/${chapterId}`, handlers, overrides, getToken())
}

export function generateArcOutline(arcId, bookId, handlers, overrides = {}) {
  const url = `${BASE}/generate/arc/${arcId}?book_id=${bookId}`
  return consumeSSE(url, handlers, overrides, getToken())
}

export function generateVolumeOutline(volumeId, bookId, handlers, overrides = {}) {
  const url = `${BASE}/generate/volume/${volumeId}?book_id=${bookId}`
  return consumeSSE(url, handlers, overrides, getToken())
}

export function generateBookOutline(bookId, handlers, overrides = {}) {
  const url = `${BASE}/generate/book?book_id=${bookId}`
  return consumeSSE(url, handlers, overrides, getToken())
}

export async function regenerateSummary(chapterId) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const resp = await fetch(`${BASE}/generate/chapter/${chapterId}/summary`, {
    method: 'POST',
    headers,
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  return resp.json()
}

// ── Preview helpers (non-streaming) ────────────────────────

async function previewFetch(url) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const resp = await fetch(url, {
    method: 'POST',
    headers,
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  return resp.json()
}

export async function previewPrompt(chapterId, bookId) {
  const data = await previewFetch(`${BASE}/generate/chapter/${chapterId}/preview?book_id=${bookId}`)
  return { data }
}

export async function previewArcPrompt(arcId, bookId) {
  return previewFetch(`${BASE}/generate/arc/${arcId}/preview?book_id=${bookId}`)
}

export async function previewVolumePrompt(volumeId, bookId) {
  return previewFetch(`${BASE}/generate/volume/${volumeId}/preview?book_id=${bookId}`)
}

export async function previewBookPrompt(bookId) {
  return previewFetch(`${BASE}/generate/book/preview?book_id=${bookId}`)
}
