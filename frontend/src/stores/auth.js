import { defineStore } from 'pinia'
import { ref } from 'vue'
import { loginRequest, registerRequest, getMe, setToken, clearToken, setUser, getUser } from '../api/auth.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(getUser())
  const token = ref(localStorage.getItem('auth_token'))
  const loading = ref(false)

  async function login(username, password) {
    loading.value = true
    try {
      const res = await loginRequest({ username, password })
      const { access_token, user: userData } = res.data
      token.value = access_token
      user.value = userData
      setToken(access_token)
      setUser(userData)
      return userData
    } finally {
      loading.value = false
    }
  }

  async function register(username, password) {
    loading.value = true
    try {
      const res = await registerRequest({ username, password })
      const { access_token, user: userData } = res.data
      token.value = access_token
      user.value = userData
      setToken(access_token)
      setUser(userData)
      return userData
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return null
    try {
      const res = await getMe()
      user.value = res.data
      setUser(res.data)
      return res.data
    } catch {
      logout()
      return null
    }
  }

  function logout() {
    token.value = null
    user.value = null
    clearToken()
  }

  function isAuthenticated() {
    return !!token.value
  }

  return {
    user,
    token,
    loading,
    login,
    register,
    fetchMe,
    logout,
    isAuthenticated,
  }
})
