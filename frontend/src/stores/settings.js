import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getGenerationSettings, updateGenerationSettings } from '../api/settings.js'
import { getBookOutline, updateBookOutline } from '../api/books.js'

export const useSettingsStore = defineStore('settings', () => {
  const previousChapterCount = ref(1)
  const outlineGenerationCount = ref(1)
  const outlineInjectionDepth = ref(1)
  const bookOutline = ref('')
  const loading = ref(false)

  async function fetchGenerationSettings() {
    loading.value = true
    try {
      const res = await getGenerationSettings()
      previousChapterCount.value = res.data.previous_chapter_count
      outlineGenerationCount.value = res.data.outline_generation_count
      outlineInjectionDepth.value = res.data.outline_injection_depth
    } catch (e) {
      console.error('Failed to fetch generation settings:', e)
    } finally {
      loading.value = false
    }
  }

  async function saveGenerationSettings() {
    loading.value = true
    try {
      await updateGenerationSettings({
        previous_chapter_count: previousChapterCount.value,
        outline_generation_count: outlineGenerationCount.value,
        outline_injection_depth: outlineInjectionDepth.value,
      })
    } finally {
      loading.value = false
    }
  }

  async function fetchBookOutline(bookId) {
    try {
      const res = await getBookOutline(bookId)
      bookOutline.value = res.data.outline || ''
    } catch (e) {
      console.error('Failed to fetch book outline:', e)
    }
  }

  async function saveBookOutline(bookId) {
    try {
      await updateBookOutline(bookId, { outline: bookOutline.value })
    } catch (e) {
      console.error('Failed to save book outline:', e)
    }
  }

  return {
    previousChapterCount,
    outlineGenerationCount,
    outlineInjectionDepth,
    bookOutline,
    loading,
    fetchGenerationSettings,
    saveGenerationSettings,
    fetchBookOutline,
    saveBookOutline,
  }
})
