<template>
  <div class="book-selector">
    <n-button
      v-if="booksStore.currentBook"
      quaternary
      class="book-selector-btn"
      @click="goToBookSelect"
    >
      <template #icon>
        <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
          <path d="M4 19.5A2.5 2.5 0 016.5 17H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </template>
      <span class="book-name">{{ booksStore.currentBook.name }}</span>
      <span class="switch-hint">切换</span>
    </n-button>
  </div>
</template>

<script setup>
import { NButton } from 'naive-ui'
import { useRouter } from 'vue-router'
import { useBooksStore } from '../../stores/books.js'

const router = useRouter()
const booksStore = useBooksStore()

function goToBookSelect() {
  booksStore.clearCurrentBook()
  router.push('/books')
}
</script>

<style scoped>
.book-selector {
  padding: 8px 12px;
  border-bottom: 1px solid #2a2520;
}
.book-selector-btn {
  width: 100%;
  justify-content: flex-start;
  color: var(--color-text-on-dark) !important;
}
.book-name {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}
.switch-hint {
  font-size: 11px;
  opacity: 0.5;
  margin-left: 4px;
}
</style>
