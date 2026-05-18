import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
})

export function getGenerationSettings() {
  return http.get('/settings/generation')
}

export function updateGenerationSettings(data) {
  return http.put('/settings/generation', data)
}

export function getBookOutline() {
  return http.get('/settings/book-outline')
}

export function updateBookOutline(data) {
  return http.put('/settings/book-outline', data)
}

// ── Book-scoped outline API ───────────────────────────────

export function getScopedBookOutline(bookId) {
  return http.get(`/books/${bookId}/outline`)
}

export function updateScopedBookOutline(bookId, data) {
  return http.put(`/books/${bookId}/outline`, data)
}
