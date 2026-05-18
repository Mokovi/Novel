import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getGenerationSettings, updateGenerationSettings } from '../api/settings.js'

export const useSettingsStore = defineStore('settings', () => {
  const previousChapterCount = ref(1)
  const autoSplitTargetWords = ref(2000)
  const loading = ref(false)

  async function fetchGenerationSettings() {
    loading.value = true
    try {
      const res = await getGenerationSettings()
      previousChapterCount.value = res.data.previous_chapter_count
      autoSplitTargetWords.value = res.data.auto_split_target_words
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
        auto_split_target_words: autoSplitTargetWords.value,
      })
    } finally {
      loading.value = false
    }
  }

  return {
    previousChapterCount,
    autoSplitTargetWords,
    loading,
    fetchGenerationSettings,
    saveGenerationSettings,
  }
})
