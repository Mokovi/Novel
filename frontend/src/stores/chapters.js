import { defineStore } from 'pinia'
import { listChapters, getChapter, listVolumes } from '../api/chapters.js'

export const useChaptersStore = defineStore('chapters', {
  state: () => ({
    volumes: [],
    chapters: [],
    currentChapter: null,
    loading: false,
  }),

  actions: {
    async fetchVolumes() {
      const res = await listVolumes()
      this.volumes = res.data
    },

    async fetchChapters(volumeId) {
      const params = volumeId ? { volume_id: volumeId } : {}
      const res = await listChapters(params)
      this.chapters = res.data
    },

    async selectChapter(id) {
      this.loading = true
      try {
        const res = await getChapter(id)
        this.currentChapter = res.data
      } finally {
        this.loading = false
      }
    },

    setCurrentChapterContent(content) {
      if (this.currentChapter) {
        this.currentChapter.content = content
      }
    },
  },
})
