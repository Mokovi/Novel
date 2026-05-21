import http from './http'

export function listLocations(bookId, params = {}) {
  return http.get('/locations', { params: { book_id: bookId, ...params } })
}

export function getLocation(id) {
  return http.get(`/locations/${id}`)
}

export function createLocation(data, bookId) {
  return http.post('/locations', data, { params: { book_id: bookId } })
}

export function updateLocation(id, data) {
  return http.put(`/locations/${id}`, data)
}

export function deleteLocation(id) {
  return http.delete(`/locations/${id}`)
}
