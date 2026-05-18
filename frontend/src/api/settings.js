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
