import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
})

export function getWorldview() {
  return http.get('/worldview')
}

export function updateWorldview(data, section) {
  const params = section ? { section } : {}
  return http.put('/worldview', data, { params })
}

export function getInjectPreview() {
  return http.get('/worldview/inject-preview')
}

// ── Book-scoped API ───────────────────────────────────────

export function getBookWorldview(bookId) {
  return http.get(`/books/${bookId}/worldview`)
}

export function updateBookWorldview(bookId, data, section) {
  const params = section ? { section } : {}
  return http.put(`/books/${bookId}/worldview`, data, { params })
}
