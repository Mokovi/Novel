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
    /**
     * Get the content of a specific section by key.
     */
    sectionContent: (state) => (key) => state.data[key] ?? null,
  },

  actions: {
    async fetch() {
      this.loading = true
      try {
        const res = await getWorldview()
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
        await updateWorldview(content, sectionKey)
      } finally {
        this.saving = false
      }
    },

    async saveAll() {
      this.saving = true
      try {
        await updateWorldview(this.data)
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
