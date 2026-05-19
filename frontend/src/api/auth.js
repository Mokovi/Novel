/**
 * Auth API — login, register, token management.
 */
import http from './http'

export function loginRequest(data) {
  return http.post('/auth/login', data)
}

export function registerRequest(data) {
  return http.post('/auth/register', data)
}

export function getMe() {
  return http.get('/auth/me')
}

export function getToken() {
  return localStorage.getItem('auth_token')
}

export function setToken(token) {
  localStorage.setItem('auth_token', token)
}

export function clearToken() {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('auth_user')
}

export function getUser() {
  const raw = localStorage.getItem('auth_user')
  if (raw) {
    try {
      return JSON.parse(raw)
    } catch {
      return null
    }
  }
  return null
}

export function setUser(user) {
  localStorage.setItem('auth_user', JSON.stringify(user))
}
