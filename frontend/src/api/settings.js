import http from './http'

export function getGenerationSettings() {
  return http.get('/settings/generation')
}

export function updateGenerationSettings(data) {
  return http.put('/settings/generation', data)
}
