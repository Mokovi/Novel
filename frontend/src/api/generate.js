/**
 * SSE generation client — uses fetch() with ReadableStream for POST + streaming.
 */
const BASE = '/api/v1'

/**
 * Generic SSE stream consumer.
 *
 * @param {string} url - Full URL to POST to
 * @param {object} handlers - { onToken(text), onStart(data), onDone(data), onError(msg) }
 * @param {object} [body] - Optional JSON body
 * @returns {AbortController}
 */
function consumeSSE(url, handlers, body) {
  const controller = new AbortController()

  ;(async () => {
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

/**
 * Start streaming generation for a chapter.
 *
 * @param {number} chapterId
 * @param {object} handlers - { onToken(text), onStart(data), onDone(data), onError(msg) }
 * @param {object} overrides - optional { temperature, max_tokens }
 * @returns {AbortController}
 */
export function generateChapter(chapterId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/generate/chapter/${chapterId}`, handlers, overrides)
}

/**
 * Start streaming arc outline generation.
 *
 * @param {number} arcId
 * @param {object} handlers
 * @param {object} [overrides]
 * @returns {AbortController}
 */
export function generateArcOutline(arcId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/generate/arc/${arcId}`, handlers, overrides)
}

/**
 * Start streaming volume outline generation.
 *
 * @param {number} volumeId
 * @param {object} handlers
 * @param {object} [overrides]
 * @returns {AbortController}
 */
export function generateVolumeOutline(volumeId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/generate/volume/${volumeId}`, handlers, overrides)
}

/**
 * Start streaming book-level outline generation.
 *
 * @param {object} handlers
 * @param {object} [overrides]
 * @returns {AbortController}
 */
export function generateBookOutline(handlers, overrides = {}) {
  return consumeSSE(`${BASE}/generate/book`, handlers, overrides)
}

/**
 * Regenerate the AI summary for a chapter (non-streaming).
 *
 * @param {number} chapterId
 * @returns {Promise<{summary: string}>}
 */
export async function regenerateSummary(chapterId) {
  const resp = await fetch(`${BASE}/generate/chapter/${chapterId}/summary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  return resp.json()
}

// ── Preview helpers (non-streaming) ────────────────────────

async function previewFetch(url) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  return resp.json()
}

/**
 * Get a prompt preview for a chapter without generating.
 *
 * @param {number} chapterId
 * @returns {Promise<{prompt: string, token_estimate: number, model: string, template_name: string}>}
 */
export async function previewPrompt(chapterId) {
  const data = await previewFetch(`${BASE}/generate/chapter/${chapterId}/preview`)
  return { data }
}

/**
 * Get a prompt preview for an arc outline.
 *
 * @param {number} arcId
 * @returns {Promise<{prompt: string, token_estimate: number, model: string, template_name: string}>}
 */
export async function previewArcPrompt(arcId) {
  return previewFetch(`${BASE}/generate/arc/${arcId}/preview`)
}

/**
 * Get a prompt preview for a volume outline.
 *
 * @param {number} volumeId
 * @returns {Promise<{prompt: string, token_estimate: number, model: string, template_name: string}>}
 */
export async function previewVolumePrompt(volumeId) {
  return previewFetch(`${BASE}/generate/volume/${volumeId}/preview`)
}

/**
 * Get a prompt preview for the book outline.
 *
 * @returns {Promise<{prompt: string, token_estimate: number, model: string, template_name: string}>}
 */
export async function previewBookPrompt() {
  return previewFetch(`${BASE}/generate/book/preview`)
}

// ── Book-scoped generate APIs ─────────────────────────────

export function generateBookOutlineScoped(bookId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/books/${bookId}/generate/book`, handlers, overrides)
}

export async function previewBookPromptScoped(bookId) {
  return previewFetch(`${BASE}/books/${bookId}/generate/book/preview`)
}

export function generateBookChapter(bookId, chapterId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/books/${bookId}/generate/chapter/${chapterId}`, handlers, overrides)
}

export async function previewBookChapterPrompt(bookId, chapterId) {
  return previewFetch(`${BASE}/books/${bookId}/generate/chapter/${chapterId}/preview`)
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

export async function previewBookArcPrompt(bookId, arcId) {
  return previewFetch(`${BASE}/books/${bookId}/generate/arc/${arcId}/preview`)
}

export function generateBookVolumeOutline(bookId, volumeId, handlers, overrides = {}) {
  return consumeSSE(`${BASE}/books/${bookId}/generate/volume/${volumeId}`, handlers, overrides)
}

export async function previewBookVolumePrompt(bookId, volumeId) {
  return previewFetch(`${BASE}/books/${bookId}/generate/volume/${volumeId}/preview`)
}
