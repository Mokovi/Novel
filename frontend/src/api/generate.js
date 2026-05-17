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
