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
