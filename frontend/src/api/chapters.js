import http from './http'

export function listVolumes(bookId) {
  return http.get('/volumes', { params: { book_id: bookId } })
}

export function listChapters(bookId, params = {}) {
  return http.get('/chapters', { params: { book_id: bookId, ...params } })
}

export function getChapter(id) {
  return http.get(`/chapters/${id}`)
}

export function createChapter(data) {
  return http.post('/chapters', data)
}

export function updateChapter(id, data) {
  return http.put(`/chapters/${id}`, data)
}

export function deleteChapter(id) {
  return http.delete(`/chapters/${id}`)
}

export function deleteVolume(id) {
  return http.delete(`/volumes/${id}`)
}

export function createVolume(data, bookId) {
  return http.post('/volumes', data, { params: { book_id: bookId } })
}

export function updateVolume(id, data) {
  return http.put(`/volumes/${id}`, data)
}

export function downloadChapter(id) {
  return http.get(`/chapters/${id}/download`, { responseType: 'blob' })
}

export function downloadAllChapters(bookId) {
  return http.get('/chapters/download-all', { params: { book_id: bookId }, responseType: 'blob' })
}

export function getChapterCharacters(id) {
  return http.get(`/chapters/${id}/characters`)
}

export function setChapterCharacters(id, characterIds) {
  return http.put(`/chapters/${id}/characters`, { character_ids: characterIds })
}

// ── Arc CRUD ─────────────────────────────────────────────

export function listArcs(bookId, params = {}) {
  return http.get('/arcs', { params: { book_id: bookId, ...params } })
}

export function getArc(id) {
  return http.get(`/arcs/${id}`)
}

export function createArc(data) {
  return http.post('/arcs', data)
}

export function updateArc(id, data) {
  return http.put(`/arcs/${id}`, data)
}

export function deleteArc(id) {
  return http.delete(`/arcs/${id}`)
}

export function reorderArcs(items) {
  return http.put('/arcs/reorder', { items })
}
