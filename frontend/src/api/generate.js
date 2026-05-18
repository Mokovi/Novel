/**
 * SSE generation client — uses fetch() with ReadableStream for POST + streaming.
 */
const BASE = '/api/v1'

/**
 * Start streaming generation for a chapter.
 *
 * @param {number} chapterId
 * @param {object} handlers - { onToken(text), onStart(data), onDone(data), onError(msg) }
 * @param {object} overrides - optional { temperature, max_tokens }
 * @returns {AbortController} - call .abort() to cancel
 */
export function generateChapter(chapterId, handlers, overrides = {}) {
  const controller = new AbortController()

  ;(async () => {
    try {
      const resp = await fetch(`${BASE}/generate/chapter/${chapterId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(overrides),
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
        buffer = lines.pop() || '' // keep incomplete line

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
 * Start unlimited generation for a chapter (auto-split into multiple chapters).
 *
 * @param {number} chapterId
 * @param {object} handlers - { onToken, onStart, onSplitting, onSummary, onDone, onError }
 * @param {object} overrides - optional { temperature }
 * @returns {AbortController}
 */
export function generateUnlimited(chapterId, handlers, overrides = {}) {
  const controller = new AbortController()

  ;(async () => {
    try {
      const resp = await fetch(`${BASE}/generate/unlimited/${chapterId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(overrides),
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
              case 'splitting':
                handlers.onSplitting?.(evt)
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
 * Get a prompt preview for a chapter without generating.
 *
 * @param {number} chapterId
 * @returns {Promise<{prompt: string, token_estimate: number, model: string, template_name: string}>}
 */
export async function previewPrompt(chapterId) {
  const resp = await fetch(`${BASE}/generate/chapter/${chapterId}/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  const data = await resp.json()
  return { data }
}
