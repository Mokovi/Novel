import http from './http'

export function listPlans() {
  return http.get('/api-plans')
}

export function getPlan(id) {
  return http.get(`/api-plans/${id}`)
}

export function createPlan(data) {
  return http.post('/api-plans', data)
}

export function updatePlan(id, data) {
  return http.put(`/api-plans/${id}`, data)
}

export function deletePlan(id) {
  return http.delete(`/api-plans/${id}`)
}
