import { defineStore } from 'pinia'
import { listBooks, getBook, createBook } from '../api/books.js'

const STORAGE_KEY = 'ai_novel_last_book_id'

export const useBooksStore = defineStore('books', {
  state: () => ({
    books: [],
    currentBook: null,
    loading: false,
  }),

  getters: {
    currentBookId(state) {
      return state.currentBook?.id ?? null
    },
  },

  actions: {
    async fetchBooks() {
      this.loading = true
      try {
        const res = await listBooks()
        this.books = res.data
      } finally {
        this.loading = false
      }
    },

    async selectBook(bookId) {
      if (this.currentBook?.id === bookId) return
      this.loading = true
      try {
        const res = await getBook(bookId)
        this.currentBook = res.data
        localStorage.setItem(STORAGE_KEY, String(bookId))
      } finally {
        this.loading = false
      }
    },

    async ensureCurrentBook() {
      // Try restoring from localStorage
      const savedId = localStorage.getItem(STORAGE_KEY)
      if (savedId) {
        try {
          await this.selectBook(Number(savedId))
          return
        } catch {
          localStorage.removeItem(STORAGE_KEY)
        }
      }
      // Fall back to first book or create a default one
      await this.fetchBooks()
      if (this.books.length > 0) {
        await this.selectBook(this.books[0].id)
      } else {
        const res = await createBook({ name: '未命名作品' })
        this.books.push(res.data)
        await this.selectBook(res.data.id)
      }
    },

    async addBook(name) {
      const res = await createBook({ name })
      this.books.push(res.data)
      return res.data
    },
  },
})
