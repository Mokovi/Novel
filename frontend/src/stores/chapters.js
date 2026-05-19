import { defineStore } from 'pinia'
import { listChapters, getChapter, listVolumes, listArcs } from '../api/chapters.js'

export const useChaptersStore = defineStore('chapters', {
  state: () => ({
    volumes: [],
    chapters: [],
    arcs: [],
    currentChapter: null,
    loading: false,
  }),

  actions: {
    async fetchVolumes(bookId) {
      const res = await listVolumes(bookId)
      this.volumes = res.data
    },

    async fetchChapters(bookId, volumeId) {
      const params = volumeId ? { volume_id: volumeId } : {}
      const res = await listChapters(bookId, params)
      this.chapters = res.data
    },

    async fetchArcs(bookId, volumeId) {
      const params = volumeId ? { volume_id: volumeId } : {}
      const res = await listArcs(bookId, params)
      this.arcs = res.data
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
