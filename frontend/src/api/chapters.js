import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
})

export function listVolumes() {
  return http.get('/volumes')
}

export function listChapters(params = {}) {
  return http.get('/chapters', { params })
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

export function createVolume(data) {
  return http.post('/volumes', data)
}

export function downloadChapter(id) {
  return http.get(`/chapters/${id}/download`, { responseType: 'blob' })
}

export function downloadAllChapters() {
  return http.get('/chapters/download-all', { responseType: 'blob' })
}

export function getChapterCharacters(id) {
  return http.get(`/chapters/${id}/characters`)
}

export function setChapterCharacters(id, characterIds) {
  return http.put(`/chapters/${id}/characters`, { character_ids: characterIds })
}
