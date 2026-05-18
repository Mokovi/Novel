import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
})

export function listBooks() {
  return http.get('/books')
}

export function getBook(id) {
  return http.get(`/books/${id}`)
}

export function createBook(data) {
  return http.post('/books', data)
}

export function updateBook(id, data) {
  return http.put(`/books/${id}`, data)
}

export function deleteBook(id) {
  return http.delete(`/books/${id}`)
}

export function getBookStats(id) {
  return http.get(`/books/${id}/stats`)
}

// Worldview sub-routes
export function getBookWorldview(bookId) {
  return http.get(`/books/${bookId}/worldview`)
}

export function updateBookWorldview(bookId, worldviewStr) {
  return http.put(`/books/${bookId}/worldview`, { worldview: worldviewStr })
}

// Outline sub-routes
export function getBookOutline(bookId) {
  return http.get(`/books/${bookId}/outline`)
}

export function updateBookOutline(bookId, outline) {
  return http.put(`/books/${bookId}/outline`, { outline })
}

// Writing style sub-routes
export function getBookWritingStyle(bookId) {
  return http.get(`/books/${bookId}/writing-style`)
}

export function updateBookWritingStyle(bookId, writingStyleStr) {
  return http.put(`/books/${bookId}/writing-style`, { writing_style: writingStyleStr })
}
