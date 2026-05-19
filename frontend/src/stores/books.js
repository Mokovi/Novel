import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listBooks, getBook, createBook as apiCreateBook } from '../api/books.js'

export const useBooksStore = defineStore('books', () => {
  const books = ref([])
  const currentBook = ref(null)
  const loading = ref(false)

  async function fetchBooks() {
    loading.value = true
    try {
      const res = await listBooks()
      books.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function selectBook(id) {
    loading.value = true
    try {
      const res = await getBook(id)
      currentBook.value = res.data
      localStorage.setItem('current_book_id', String(id))
    } finally {
      loading.value = false
    }
  }

  function clearCurrentBook() {
    currentBook.value = null
    localStorage.removeItem('current_book_id')
  }

  async function createBook(data) {
    const res = await apiCreateBook(data)
    books.value.push(res.data)
    return res.data
  }

  return {
    books,
    currentBook,
    loading,
    fetchBooks,
    selectBook,
    clearCurrentBook,
    createBook,
  }
})
