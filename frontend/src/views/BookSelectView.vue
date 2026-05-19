<template>
  <div class="book-select-container">
    <div class="book-select-header">
      <h1 class="book-select-title">选择作品</h1>
      <p class="book-select-subtitle">选择或创建一个作品开始写作</p>
    </div>

    <div class="book-grid">
      <div
        v-for="book in booksStore.books"
        :key="book.id"
        class="book-card"
        @click="openBook(book.id)"
      >
        <div class="book-card-icon">
          <img v-if="book.cover_image" :src="book.cover_image" class="book-cover-img" />
          <span v-else class="book-icon-text">{{ book.name.charAt(0) }}</span>
        </div>
        <div class="book-card-info">
          <h3 class="book-card-title">{{ book.name }}</h3>
          <p class="book-card-desc">{{ book.description || '暂无描述' }}</p>
        </div>
      </div>

      <!-- Create new book card -->
      <div class="book-card book-card-new" @click="showCreateDialog = true">
        <div class="book-card-icon new-icon">
          <span class="plus-sign">+</span>
        </div>
        <div class="book-card-info">
          <h3 class="book-card-title">创建新作品</h3>
          <p class="book-card-desc">开始一段新的创作旅程</p>
        </div>
      </div>
    </div>

    <!-- Create book dialog -->
    <n-modal v-model:show="showCreateDialog" title="创建新作品" preset="card" style="width: 420px">
      <n-form ref="formRef" :model="newBook" :rules="rules">
        <n-form-item label="作品名称" path="name">
          <n-input v-model:value="newBook.name" placeholder="输入作品名称" />
        </n-form-item>
        <n-form-item label="作品描述" path="description">
          <n-input
            v-model:value="newBook.description"
            type="textarea"
            placeholder="可选：简短描述你的作品"
            :rows="3"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="showCreateDialog = false" style="margin-right: 12px">取消</n-button>
        <n-button type="primary" :loading="creating" @click="handleCreate">创建</n-button>
      </template>
    </n-modal>

  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NForm, NFormItem, NInput, NModal, useMessage } from 'naive-ui'
import { useBooksStore } from '../stores/books.js'

const router = useRouter()
const booksStore = useBooksStore()
const message = useMessage()
const formRef = ref(null)
const showCreateDialog = ref(false)
const creating = ref(false)

const newBook = reactive({
  name: '',
  description: '',
})

const rules = {
  name: [{ required: true, message: '请输入作品名称', trigger: 'blur' }],
}

async function handleCreate() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  creating.value = true
  try {
    const book = await booksStore.createBook({
      name: newBook.name,
      description: newBook.description,
    })
    message.success('作品创建成功')
    showCreateDialog.value = false
    newBook.name = ''
    newBook.description = ''
    router.push(`/books/${book.id}/outline`)
  } catch (e) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

function openBook(id) {
  router.push(`/books/${id}/outline`)
}

onMounted(() => {
  booksStore.fetchBooks()
})
</script>

<style scoped>
.book-select-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 48px 24px;
}
.book-select-header {
  text-align: center;
  margin-bottom: 40px;
}
.book-select-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--color-text);
}
.book-select-subtitle {
  color: var(--color-text-muted);
  margin: 0;
  font-size: 14px;
}
.book-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}
.book-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.book-card:hover {
  border-color: var(--color-accent);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}
.book-card-new {
  border-style: dashed;
  opacity: 0.7;
}
.book-card-new:hover {
  opacity: 1;
}
.book-card-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-hover));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}
.book-cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 10px;
}
.book-icon-text {
  color: white;
  font-size: 20px;
  font-weight: 700;
}
.new-icon {
  background: var(--color-bg-module);
  border: 2px dashed var(--color-border);
}
.plus-sign {
  font-size: 24px;
  color: var(--color-text-muted);
  font-weight: 300;
}
.book-card-info {
  flex: 1;
  min-width: 0;
}
.book-card-title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}
.book-card-desc {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
