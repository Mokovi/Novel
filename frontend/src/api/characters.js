import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
})

export function listCharacters(params = {}) {
  return http.get('/characters', { params })
}

export function getCharacter(id) {
  return http.get(`/characters/${id}`)
}

export function createCharacter(data) {
  return http.post('/characters', data)
}

export function updateCharacter(id, data) {
  return http.put(`/characters/${id}`, data)
}

export function deleteCharacter(id) {
  return http.delete(`/characters/${id}`)
}

export function getRelationsGraph() {
  return http.get('/characters/relations')
}

export function createRelation(data) {
  return http.post('/characters/relations', data)
}

export function updateRelation(id, data) {
  return http.put(`/characters/relations/${id}`, data)
}

export function deleteRelation(id) {
  return http.delete(`/characters/relations/${id}`)
}

// ── Book-scoped API ───────────────────────────────────────

export function listBookCharacters(bookId, params = {}) {
  return http.get(`/books/${bookId}/characters`, { params })
}

export function createBookCharacter(bookId, data) {
  return http.post(`/books/${bookId}/characters`, data)
}

export function getBookRelationsGraph(bookId) {
  return http.get(`/books/${bookId}/characters/relations`)
}
