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
        @contextmenu.prevent="onContextMenu($event, book)"
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

    <!-- Context menu -->
    <ContextMenu ref="contextMenuRef" :options="contextMenuOptions" @select="onContextMenuSelect" />

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

    <!-- Edit book dialog -->
    <n-modal v-model:show="showEditDialog" title="编辑作品" preset="card" style="width: 420px">
      <n-form :model="editForm" :rules="editRules" ref="editFormRef">
        <n-form-item label="作品名称" path="name">
          <n-input v-model:value="editForm.name" placeholder="输入作品名称" />
        </n-form-item>
        <n-form-item label="作品描述" path="description">
          <n-input
            v-model:value="editForm.description"
            type="textarea"
            placeholder="可选：简短描述你的作品"
            :rows="3"
          />
        </n-form-item>
        <n-form-item label="封面图片">
          <div class="cover-upload-area">
            <img v-if="editCoverPreview" :src="editCoverPreview" class="cover-preview" />
            <div v-else class="cover-placeholder">暂无封面</div>
            <div class="cover-upload-actions">
              <input
                ref="fileInputRef"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                style="display: none"
                @change="onCoverFileChange"
              />
              <n-button size="small" @click="fileInputRef?.click()">
                {{ editCoverPreview ? '更换图片' : '上传图片' }}
              </n-button>
              <span v-if="editCoverFile" class="cover-file-name">{{ editCoverFile.name }}</span>
            </div>
            <p class="cover-hint">支持 JPG、PNG、WebP 格式，建议 400×600 像素</p>
          </div>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="showEditDialog = false" style="margin-right: 12px">取消</n-button>
        <n-button type="primary" :loading="saving" @click="handleEditSave">保存</n-button>
      </template>
    </n-modal>

    <!-- Delete confirmation dialog -->
    <n-modal v-model:show="showDeleteDialog" title="确认删除" preset="card" style="width: 380px">
      <p class="delete-warning">
        确定删除「<strong>{{ deleteTarget?.name }}</strong>」吗？此操作不可撤销，作品下的所有章节数据将一并删除。
      </p>
      <template #footer>
        <n-button @click="showDeleteDialog = false" style="margin-right: 12px">取消</n-button>
        <n-button type="error" :loading="deleting" @click="handleDeleteConfirm">确认删除</n-button>
      </template>
    </n-modal>

  </div>
</template>

<script setup>
import { onMounted, reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NForm, NFormItem, NInput, NModal, useMessage } from 'naive-ui'
import { useBooksStore } from '../stores/books.js'
import ContextMenu from '../components/common/ContextMenu.vue'

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

// Context menu
const contextMenuRef = ref(null)
const contextTarget = ref(null)

const contextMenuOptions = computed(() => [
  { label: '编辑信息', key: 'edit' },
  { label: '更换封面', key: 'change-cover' },
  { label: '删除作品', key: 'delete', danger: true },
])

function onContextMenu(e, book) {
  contextTarget.value = book
  contextMenuRef.value?.show(e.clientX, e.clientY)
}

function onContextMenuSelect(key) {
  const book = contextTarget.value
  if (!book) return
  if (key === 'edit') {
    openEditDialog(book)
  } else if (key === 'change-cover') {
    openEditDialog(book, true)
  } else if (key === 'delete') {
    openDeleteDialog(book)
  }
}

// Edit dialog
const showEditDialog = ref(false)
const editFormRef = ref(null)
const saving = ref(false)
const editForm = reactive({ name: '', description: '' })
const editBookId = ref(null)
const editCoverPreview = ref('')
const editCoverFile = ref(null)
const fileInputRef = ref(null)
const editFocusCover = ref(false)

const editRules = {
  name: [{ required: true, message: '请输入作品名称', trigger: 'blur' }],
}

function openEditDialog(book, focusCover = false) {
  editBookId.value = book.id
  editForm.name = book.name
  editForm.description = book.description || ''
  editCoverPreview.value = book.cover_image || ''
  editCoverFile.value = null
  editFocusCover.value = focusCover
  showEditDialog.value = true
}

function onCoverFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  editCoverFile.value = file
  const reader = new FileReader()
  reader.onload = (ev) => {
    editCoverPreview.value = ev.target.result
  }
  reader.readAsDataURL(file)
}

async function handleEditSave() {
  try {
    await editFormRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await booksStore.updateBook(editBookId.value, {
      name: editForm.name,
      description: editForm.description,
    })
    if (editCoverFile.value) {
      await booksStore.uploadCover(editBookId.value, editCoverFile.value)
    }
    message.success('作品信息已更新')
    showEditDialog.value = false
  } catch (e) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// Delete dialog
const showDeleteDialog = ref(false)
const deleteTarget = ref(null)
const deleting = ref(false)

function openDeleteDialog(book) {
  deleteTarget.value = book
  showDeleteDialog.value = true
}

async function handleDeleteConfirm() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await booksStore.deleteBook(deleteTarget.value.id)
    message.success('作品已删除')
    showDeleteDialog.value = false
    deleteTarget.value = null
  } catch (e) {
    message.error(e.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
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

/* Cover upload area */
.cover-upload-area {
  width: 100%;
}
.cover-preview {
  width: 120px;
  height: 160px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  display: block;
  margin-bottom: 8px;
}
.cover-placeholder {
  width: 120px;
  height: 160px;
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-size: 13px;
  margin-bottom: 8px;
}
.cover-upload-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.cover-file-name {
  font-size: 12px;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}
.cover-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

/* Delete warning */
.delete-warning {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
}
</style>
