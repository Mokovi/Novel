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

async function previewFetch(url, body) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const resp = await fetch(url, {
    method: 'POST',
    headers,
    body: body ? JSON.stringify(body) : '{}',
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  return resp.json()
}

export async function previewPrompt(chapterId, bookId, injectionOverrides) {
  const body = injectionOverrides ? { injection_overrides: injectionOverrides } : undefined
  const data = await previewFetch(`${BASE}/generate/chapter/${chapterId}/preview?book_id=${bookId}`, body)
  return { data }
}

export async function previewArcPrompt(arcId, bookId, injectionOverrides) {
  const body = injectionOverrides ? { injection_overrides: injectionOverrides } : undefined
  return previewFetch(`${BASE}/generate/arc/${arcId}/preview?book_id=${bookId}`, body)
}

export async function previewVolumePrompt(volumeId, bookId, injectionOverrides) {
  const body = injectionOverrides ? { injection_overrides: injectionOverrides } : undefined
  return previewFetch(`${BASE}/generate/volume/${volumeId}/preview?book_id=${bookId}`, body)
}

export async function previewBookPrompt(bookId, injectionOverrides) {
  const body = injectionOverrides ? { injection_overrides: injectionOverrides } : undefined
  return previewFetch(`${BASE}/generate/book/preview?book_id=${bookId}`, body)
}

export function generateWorldview(bookId, handlers, overrides = {}) {
  const url = `${BASE}/generate/worldview?book_id=${bookId}`
  return consumeSSE(url, handlers, overrides, getToken())
}

export async function previewWorldviewPrompt(bookId, injectionOverrides) {
  const body = injectionOverrides ? { injection_overrides: injectionOverrides } : undefined
  return previewFetch(`${BASE}/generate/worldview/preview?book_id=${bookId}`, body)
}

// ── Injection metadata helpers ────────────────────────────

async function injectionFetch(url) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const resp = await fetch(url, {
    method: 'POST',
    headers,
    body: '{}',
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  return resp.json()
}

export async function fetchChapterInjections(chapterId, bookId) {
  return injectionFetch(`${BASE}/generate/chapter/${chapterId}/injections?book_id=${bookId}`)
}

export async function fetchArcInjections(arcId, bookId) {
  return injectionFetch(`${BASE}/generate/arc/${arcId}/injections?book_id=${bookId}`)
}

export async function fetchVolumeInjections(volumeId, bookId) {
  return injectionFetch(`${BASE}/generate/volume/${volumeId}/injections?book_id=${bookId}`)
}

export async function fetchBookInjections(bookId) {
  return injectionFetch(`${BASE}/generate/book/injections?book_id=${bookId}`)
}

export async function fetchWorldviewInjections(bookId) {
  return injectionFetch(`${BASE}/generate/worldview/injections?book_id=${bookId}`)
}

// ── Map generation ──────────────────────────────────────────

export function generateMap(bookId, handlers, overrides = {}) {
  const url = `${BASE}/generate/map?book_id=${bookId}`
  return consumeSSE(url, handlers, overrides, getToken())
}

export async function previewMapPrompt(bookId, injectionOverrides) {
  const body = injectionOverrides ? { injection_overrides: injectionOverrides } : undefined
  return previewFetch(`${BASE}/generate/map/preview?book_id=${bookId}`, body)
}

export async function fetchMapInjections(bookId) {
  return injectionFetch(`${BASE}/generate/map/injections?book_id=${bookId}`)
}

// ── Character generation ────────────────────────────────────

export function generateCharacters(bookId, handlers, overrides = {}) {
  const url = `${BASE}/generate/characters?book_id=${bookId}`
  return consumeSSE(url, handlers, overrides, getToken())
}

export async function fetchCharacterInjections(bookId) {
  return injectionFetch(`${BASE}/generate/characters/injections?book_id=${bookId}`)
}

// ── Book-scoped generate APIs ─────────────────────────────

export function generateBookOutlineScoped(bookId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/books/${bookId}/generate/book`, handlers, overrides)
}

export async function previewBookPromptScoped(bookId, injectionOverrides) {
  const body = injectionOverrides ? { injection_overrides: injectionOverrides } : undefined
  return previewFetch(`${BASE}/books/${bookId}/generate/book/preview`, body)
}

export function generateBookChapter(bookId, chapterId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/books/${bookId}/generate/chapter/${chapterId}`, handlers, overrides)
}

export async function previewBookChapterPrompt(bookId, chapterId, injectionOverrides) {
  const body = injectionOverrides ? { injection_overrides: injectionOverrides } : undefined
  return previewFetch(`${BASE}/books/${bookId}/generate/chapter/${chapterId}/preview`, body)
}

export async function regenerateBookChapterSummary(bookId, chapterId) {
  const resp = await fetch(`${BASE}/books/${bookId}/generate/chapter/${chapterId}/summary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  return resp.json()
}

export function generateBookArcOutline(bookId, arcId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/books/${bookId}/generate/arc/${arcId}`, handlers, overrides)
}

export async function previewBookArcPrompt(bookId, arcId, injectionOverrides) {
  const body = injectionOverrides ? { injection_overrides: injectionOverrides } : undefined
  return previewFetch(`${BASE}/books/${bookId}/generate/arc/${arcId}/preview`, body)
}

export function generateBookVolumeOutline(bookId, volumeId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/books/${bookId}/generate/volume/${volumeId}`, handlers, overrides)
}

export async function previewBookVolumePrompt(bookId, volumeId, injectionOverrides) {
  const body = injectionOverrides ? { injection_overrides: injectionOverrides } : undefined
  return previewFetch(`${BASE}/books/${bookId}/generate/volume/${volumeId}/preview`, body)
}
