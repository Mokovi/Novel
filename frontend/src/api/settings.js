import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
})

export function listModelRoutes() {
  return http.get('/model-routes')
}

export function updateModelRoute(taskKey, data) {
  return http.put(`/model-routes/${taskKey}`, data)
}

export function testModelRoute(taskKey) {
  return http.post(`/model-routes/${taskKey}/test`)
}
