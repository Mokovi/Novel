<template>
  <div class="book-selector">
    <n-popselect
      v-model:value="selectedId"
      :options="bookOptions"
      trigger="click"
      @update:value="onSelect"
      :width="200"
    >
      <div class="book-selector-trigger">
        <span class="book-name">{{ currentName }}</span>
        <span class="book-arrow">▾</span>
      </div>
    </n-popselect>

    <!-- Add Book Modal -->
    <n-modal v-model:show="showAddModal" preset="card" title="新建作品" style="width: 400px">
      <n-input
        v-model:value="newBookName"
        placeholder="输入作品名称"
        @keyup.enter="confirmAdd"
      />
      <template #footer>
        <n-button type="primary" :loading="adding" @click="confirmAdd">创建</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useBooksStore } from '../../stores/books.js'

const router = useRouter()
const booksStore = useBooksStore()

const showAddModal = ref(false)
const newBookName = ref('')
const adding = ref(false)

const selectedId = computed({
  get: () => booksStore.currentBookId,
  set: () => {},
})

const currentName = computed(() => {
  return booksStore.currentBook?.name || '选择作品'
})

const bookOptions = computed(() => {
  const options = booksStore.books.map((b) => ({
    label: b.name,
    value: b.id,
  }))
  options.push({
    label: '---',
    value: null,
    disabled: true,
  })
  options.push({
    label: '✚ 新建作品',
    value: '__add__',
  })
  return options
})

function onSelect(val) {
  if (val === '__add__') {
    showAddModal.value = true
    return
  }
  if (val && val !== booksStore.currentBookId) {
    router.push(`/books/${val}/outline`)
  }
}

async function confirmAdd() {
  if (!newBookName.value.trim()) return
  adding.value = true
  try {
    const book = await booksStore.addBook(newBookName.value.trim())
    newBookName.value = ''
    showAddModal.value = false
    router.push(`/books/${book.id}/outline`)
  } finally {
    adding.value = false
  }
}
</script>

<style scoped>
.book-selector {
  padding: 8px 12px;
}

.book-selector-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 6px;
  transition: background var(--transition-base);
}

.book-selector-trigger:hover {
  background: var(--color-bg-hover, rgba(255, 255, 255, 0.05));
}

.book-name {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}

.book-arrow {
  font-size: 10px;
  color: var(--color-text-secondary);
  margin-left: 6px;
}
</style>
