import { defineStore } from 'pinia'
import { ref } from 'vue'
import { verifyAdmin } from '../api/admin.js'

export const useAdminStore = defineStore('admin', () => {
  const isAdmin = ref(false)

  async function verify(password) {
    const data = await verifyAdmin(password)
    if (data.valid) {
      isAdmin.value = true
      return true
    }
    return false
  }

  function logout() {
    isAdmin.value = false
  }

  return { isAdmin, verify, logout }
})
