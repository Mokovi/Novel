<template>
  <div class="dashboard">
    <section class="hero">
      <h1 class="hero-title">我的作品</h1>
      <p class="hero-subtitle">选择一部作品开始创作，或创建新的作品</p>
    </section>

    <div class="toolbar">
      <n-button type="primary" @click="showCreate = true">
        <template #icon>+</template>
        新建作品
      </n-button>
    </div>

    <!-- Book Grid -->
    <section v-if="booksStore.loading" class="loading-state">
      <n-spin size="medium" />
    </section>

    <section v-else-if="books.length === 0" class="empty-state">
      <p>还没有作品，点击上方按钮创建你的第一部作品。</p>
    </section>

    <section v-else class="book-grid">
      <div
        v-for="book in books"
        :key="book.id"
        class="book-card"
        @click="openBook(book.id)"
      >
        <div class="book-card-header">
          <h3 class="book-name">{{ book.name }}</h3>
          <n-button
            quaternary
            circle
            size="tiny"
            class="delete-btn"
            @click.stop="confirmDelete(book)"
          >
            <template #icon>✕</template>
          </n-button>
        </div>
        <p v-if="book.description" class="book-desc">{{ book.description }}</p>
        <div class="book-meta">
          <span>更新于 {{ formatDate(book.updated_at) }}</span>
        </div>
      </div>
    </section>

    <!-- Create Book Modal -->
    <n-modal v-model:show="showCreate" preset="card" title="新建作品" style="width: 400px">
      <n-input v-model:value="newName" placeholder="输入作品名称" @keyup.enter="createBook" />
      <template #footer>
        <n-button type="primary" :loading="creating" @click="createBook">创建</n-button>
      </template>
    </n-modal>

    <!-- Delete Confirm Dialog -->
    <n-modal v-model:show="showDelete" preset="dialog" type="warning" title="确认删除"
      :content="`确定要删除「${deletingBook?.name}」吗？此操作不可撤销，所有关联数据将被清除。`"
      positive-text="删除"
      negative-text="取消"
      @positive-click="doDelete"
      @negative-click="showDelete = false"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useBooksStore } from '../stores/books.js'
import { deleteBook } from '../api/books.js'

const router = useRouter()
const booksStore = useBooksStore()

const books = computed(() => booksStore.books)
const showCreate = ref(false)
const newName = ref('')
const creating = ref(false)
const showDelete = ref(false)
const deletingBook = ref(null)

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function openBook(id) {
  router.push(`/books/${id}/outline`)
}

async function createBook() {
  if (!newName.value.trim()) return
  creating.value = true
  try {
    const book = await booksStore.addBook(newName.value.trim())
    newName.value = ''
    showCreate.value = false
    openBook(book.id)
  } finally {
    creating.value = false
  }
}

function confirmDelete(book) {
  deletingBook.value = book
  showDelete.value = true
}

async function doDelete() {
  if (!deletingBook.value) return
  try {
    await deleteBook(deletingBook.value.id)
    await booksStore.fetchBooks()
  } finally {
    showDelete.value = false
    deletingBook.value = null
  }
}

onMounted(async () => {
  await booksStore.fetchBooks()
})
</script>

<style scoped>
.dashboard {
  max-width: 900px;
  margin: 0 auto;
}

.hero {
  margin-bottom: 24px;
}

.hero-title {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.hero-subtitle {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
}

.toolbar {
  margin-bottom: 24px;
}

.book-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.book-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  cursor: pointer;
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.book-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-card-hover);
}

.book-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.book-name {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.delete-btn {
  opacity: 0;
  transition: opacity var(--transition-base);
}

.book-card:hover .delete-btn {
  opacity: 1;
}

.book-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
  line-height: 1.5;
}

.book-meta {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-secondary);
}
</style>
