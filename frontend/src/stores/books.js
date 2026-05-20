import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listBooks, getBook, createBook as apiCreateBook, updateBook as apiUpdateBook, deleteBook as apiDeleteBook, uploadCover as apiUploadCover } from '../api/books.js'

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

  async function updateBook(id, data) {
    const res = await apiUpdateBook(id, data)
    const idx = books.value.findIndex(b => b.id === id)
    if (idx !== -1) books.value[idx] = { ...books.value[idx], ...res.data }
    if (currentBook.value?.id === id) currentBook.value = { ...currentBook.value, ...res.data }
    return res.data
  }

  async function deleteBook(id) {
    await apiDeleteBook(id)
    books.value = books.value.filter(b => b.id !== id)
    if (currentBook.value?.id === id) clearCurrentBook()
  }

  async function uploadCover(bookId, file) {
    const res = await apiUploadCover(bookId, file, true)
    const idx = books.value.findIndex(b => b.id === bookId)
    if (idx !== -1) books.value[idx] = { ...books.value[idx], cover_image: res.data.cover_image }
    if (currentBook.value?.id === bookId) currentBook.value = { ...currentBook.value, cover_image: res.data.cover_image }
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
    updateBook,
    deleteBook,
    uploadCover,
  }
})
