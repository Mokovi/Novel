import { defineStore } from 'pinia'
import { getWorldview, updateWorldview, getInjectPreview } from '../api/worldview.js'
import * as booksApi from '../api/books.js'

export const useWorldviewStore = defineStore('worldview', {
  state: () => ({
    data: {},
    loading: false,
    saving: false,
    previewText: '',
    previewTokenEstimate: 0,
    previewLoading: false,
    _bookId: null,
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
    setBookId(bookId) {
      this._bookId = bookId
    },

    async fetch() {
      this.loading = true
      try {
        const res = this._bookId
          ? await booksApi.getBookWorldview(this._bookId)
          : await getWorldview()
        this.data = res.data
      } finally {
        this.loading = false
      }
    },

    async saveSection(sectionKey) {
      const content = this.data[sectionKey]
      if (content === undefined) return
      this.saving = true
      try {
        if (this._bookId) {
          const full = { ...this.data }
          full[sectionKey] = content
          await booksApi.updateBookWorldview(this._bookId, JSON.stringify(full))
        } else {
          await updateWorldview(content, sectionKey)
        }
      } finally {
        this.saving = false
      }
    },

    async saveAll() {
      this.saving = true
      try {
        if (this._bookId) {
          await booksApi.updateBookWorldview(this._bookId, JSON.stringify(this.data))
        } else {
          await updateWorldview(this.data)
        }
      } finally {
        this.saving = false
      }
    },

    async fetchPreview() {
      this.previewLoading = true
      try {
        const res = await getInjectPreview()
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
