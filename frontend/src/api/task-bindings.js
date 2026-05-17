import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
})

export function listTaskBindings() {
  return http.get('/task-bindings')
}

export function updateTaskBinding(taskKey, data) {
  return http.put(`/task-bindings/${taskKey}`, data)
}

export function deleteTaskBinding(taskKey) {
  return http.delete(`/task-bindings/${taskKey}`)
}
