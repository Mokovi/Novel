import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
})

export function listModelApis() {
  return http.get('/model-apis')
}

export function createModelApi(data) {
  return http.post('/model-apis', data)
}

export function updateModelApi(id, data) {
  return http.put(`/model-apis/${id}`, data)
}

export function deleteModelApi(id) {
  return http.delete(`/model-apis/${id}`)
}

export function testModelApi(id) {
  return http.post(`/model-apis/${id}/test`)
}
