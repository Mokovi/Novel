/**
 * Books API.
 */
import http from './http'

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

export function getBookWorldview(id) {
  return http.get(`/books/${id}/worldview`)
}

export function updateBookWorldview(id, data) {
  return http.put(`/books/${id}/worldview`, data)
}

export function getBookWritingStyle(id) {
  return http.get(`/books/${id}/writing-style`)
}

export function updateBookWritingStyle(id, data) {
  return http.put(`/books/${id}/writing-style`, data)
}

export function getBookOutline(id) {
  return http.get(`/books/${id}/outline`)
}

export function updateBookOutline(id, data) {
  return http.put(`/books/${id}/outline`, data)
}
