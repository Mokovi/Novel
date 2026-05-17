import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
})

export function listTemplates() {
  return http.get('/templates')
}

export function getTemplate(fileName) {
  return http.get(`/templates/${encodeURIComponent(fileName)}`)
}

export function createTemplate(data) {
  return http.post('/templates', data)
}

export function updateTemplate(fileName, data) {
  return http.put(`/templates/${encodeURIComponent(fileName)}`, data)
}

export function deleteTemplate(fileName) {
  return http.delete(`/templates/${encodeURIComponent(fileName)}`)
}

export function buildPreview(fileName, variables) {
  return http.post('/templates/build-preview', { file_name: fileName, variables })
}
