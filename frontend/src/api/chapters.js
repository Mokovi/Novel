import axios from 'axios'

const http = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
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

export function createVolume(data) {
  return http.post('/volumes', data)
}
