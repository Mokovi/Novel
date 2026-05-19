import http from './http'

export function getWorldview(bookId) {
  const params = bookId ? { book_id: bookId } : {}
  return http.get('/worldview', { params })
}

export function updateWorldview(data, section, bookId) {
  const params = {}
  if (section) params.section = section
  if (bookId) params.book_id = bookId
  return http.put('/worldview', data, { params })
}

export function getInjectPreview(bookId) {
  const params = bookId ? { book_id: bookId } : {}
  return http.get('/worldview/inject-preview', { params })
}

// ── Book-scoped API ───────────────────────────────────────

export function getBookWorldview(bookId) {
  return http.get(`/books/${bookId}/worldview`)
}

export function updateBookWorldview(bookId, data, section) {
  const params = section ? { section } : {}
  return http.put(`/books/${bookId}/worldview`, data, { params })
}
