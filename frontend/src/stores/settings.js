import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getGenerationSettings, updateGenerationSettings, getBookOutline, updateBookOutline } from '../api/settings.js'

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

  async function fetchBookOutline() {
    try {
      const res = await getBookOutline()
      bookOutline.value = res.data.book_outline || ''
    } catch (e) {
      console.error('Failed to fetch book outline:', e)
    }
  }

  async function saveBookOutline() {
    try {
      await updateBookOutline({ book_outline: bookOutline.value })
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
