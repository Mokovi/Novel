import { defineStore } from 'pinia'
import {
  getChapter,
  listVolumes,
  listChapters,
  listArcs,
  listBookVolumes,
  listBookChapters,
  listBookArcs,
} from '../api/chapters.js'

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
      const res = bookId ? await listBookVolumes(bookId) : await listVolumes()
      this.volumes = res.data
    },

    async fetchChapters(volumeId, bookId) {
      const params = volumeId ? { volume_id: volumeId } : {}
      const res = bookId
        ? await listBookChapters(bookId, params)
        : await listChapters(params)
      this.chapters = res.data
    },

    async fetchArcs(volumeId, bookId) {
      const params = volumeId ? { volume_id: volumeId } : {}
      const res = bookId
        ? await listBookArcs(bookId, params)
        : await listArcs(params)
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
