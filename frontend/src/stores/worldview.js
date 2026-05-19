import { defineStore } from 'pinia'
import { getWorldview, updateWorldview, getInjectPreview } from '../api/worldview.js'

export const useWorldviewStore = defineStore('worldview', {
  state: () => ({
    worldview: '',
    loading: false,
    saving: false,
    previewText: '',
    previewTokenEstimate: 0,
    previewLoading: false,
  }),

  actions: {
    async fetch(bookId) {
      this.loading = true
      try {
        const res = await getWorldview(bookId)
        this.worldview = res.data?.worldview || res.data || ''
      } finally {
        this.loading = false
      }
    },

    async saveAll(bookId) {
      this.saving = true
      try {
        await updateWorldview({ worldview: this.worldview }, null, bookId)
      } finally {
        this.saving = false
      }
    },

    async fetchPreview(bookId) {
      this.previewLoading = true
      try {
        const res = await getInjectPreview(bookId)
        this.previewText = res.data.text
        this.previewTokenEstimate = res.data.token_estimate
      } finally {
        this.previewLoading = false
      }
    },
  },
})
