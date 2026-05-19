import { defineStore } from 'pinia'
import { getWorldview, updateWorldview, getInjectPreview } from '../api/worldview.js'

export const useWorldviewStore = defineStore('worldview', {
  state: () => ({
    data: {},
    loading: false,
    saving: false,
    previewText: '',
    previewTokenEstimate: 0,
    previewLoading: false,
  }),

  getters: {
    sections: (state) => {
      return Object.keys(state.data).map((key) => ({
        key,
        label: key,
        content: state.data[key],
      }))
    },
    isGlossary: (state) => (key) => key === '术语表',
    sectionContent: (state) => (key) => state.data[key] ?? null,
  },

  actions: {
    async fetch(bookId) {
      this.loading = true
      try {
        const res = await getWorldview(bookId)
        this.data = res.data
      } finally {
        this.loading = false
      }
    },

    async saveSection(sectionKey, bookId) {
      const content = this.data[sectionKey]
      if (content === undefined) return
      this.saving = true
      try {
        await updateWorldview(content, sectionKey, bookId)
      } finally {
        this.saving = false
      }
    },

    async saveAll(bookId) {
      this.saving = true
      try {
        await updateWorldview(this.data, null, bookId)
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

    updateSection(sectionKey, content) {
      this.data[sectionKey] = content
    },

    addGlossaryItem() {
      const glossary = this.data['术语表']
      if (Array.isArray(glossary)) {
        glossary.push({ term: '', definition: '' })
      } else {
        this.data['术语表'] = [{ term: '', definition: '' }]
      }
    },

    removeGlossaryItem(index) {
      const glossary = this.data['术语表']
      if (Array.isArray(glossary)) {
        glossary.splice(index, 1)
      }
    },
  },
})
