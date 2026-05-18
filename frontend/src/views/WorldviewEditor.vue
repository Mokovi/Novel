<template>
  <div class="worldview-editor">
    <!-- Header -->
    <div class="editor-header">
      <h2>世界观设定</h2>
      <div class="header-actions">
        <n-button size="small" quaternary @click="refreshData">
          <template #icon><n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></n-icon></template>
        </n-button>
        <n-button size="small" @click="showPreview = true">
          <template #icon><n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" fill="none"/></svg></n-icon></template>
          注入预览
        </n-button>
      </div>
    </div>

    <!-- Loading spinner -->
    <div v-if="store.loading" class="loading-center">
      <n-spin size="medium" />
    </div>

    <!-- Tabs -->
    <n-tabs v-else type="line" animated class="section-tabs">
      <n-tab-pane
        v-for="sec in store.sections"
        :key="sec.key"
        :tab="sec.label"
        :name="sec.key"
      >
        <div class="section-content">
          <!-- Glossary (array of {term, definition}) -->
          <template v-if="sec.key === '术语表'">
            <GlossaryEditor
              :items="glossaryItems"
              @update:items="onGlossaryUpdate"
            />
          </template>

          <!-- Array of objects -->
          <template v-else-if="Array.isArray(sec.content)">
            <ArrayEditor
              :value="sec.content"
              @update:value="onSectionUpdate(sec.key, $event)"
            />
          </template>

          <!-- Object or other -->
          <template v-else>
            <ObjectEditor
              :value="sec.content"
              @update:value="onSectionUpdate(sec.key, $event)"
            />
          </template>

          <!-- Save button per section -->
          <div class="section-footer">
            <n-button
              type="primary"
              size="small"
              :loading="store.saving"
              :disabled="!isSectionDirty(sec.key)"
              @click="saveSection(sec.key)"
            >
              保存 {{ sec.label }}
            </n-button>
          </div>
        </div>
      </n-tab-pane>
    </n-tabs>

    <!-- Inject preview drawer -->
    <n-drawer v-model:show="showPreview" width="520" placement="right">
      <n-drawer-content title="设定注入预览" closable>
        <template #header-extra>
          <n-tag v-if="preview.token_estimate" type="info" size="small">
            ~{{ preview.token_estimate }} tokens
          </n-tag>
        </template>

        <div v-if="store.previewLoading" class="loading-center">
          <n-spin size="small" />
        </div>

        <n-empty v-else-if="!store.previewText" description="暂无设定内容" />

        <pre v-else class="preview-textarea">{{ store.previewText }}</pre>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useWorldviewStore } from '../stores/worldview.js'
import { useBooksStore } from '../stores/books.js'
import GlossaryEditor from '../components/worldview/GlossaryEditor.vue'
import ObjectEditor from '../components/worldview/ObjectEditor.vue'
import ArrayEditor from '../components/worldview/ArrayEditor.vue'

const route = useRoute()
const store = useWorldviewStore()
const booksStore = useBooksStore()
const message = useMessage()

const bookId = computed(() => {
  return route.params.bookId ? Number(route.params.bookId) : booksStore.currentBookId
})

const showPreview = ref(false)
const dirtySections = ref(new Set())

const glossaryItems = computed({
  get: () => {
    const g = store.data['术语表']
    return Array.isArray(g) ? g : []
  },
  set: (val) => {
    store.updateSection('术语表', val)
    dirtySections.value.add('术语表')
  },
})

const preview = computed(() => ({
  text: store.previewText,
  token_estimate: store.previewTokenEstimate,
}))

function isSectionDirty(key) {
  return dirtySections.value.has(key)
}

function onSectionUpdate(key, value) {
  store.updateSection(key, value)
  dirtySections.value.add(key)
}

function onGlossaryUpdate(items) {
  glossaryItems.value = items
}

async function saveSection(key) {
  await store.saveSection(key)
  dirtySections.value.delete(key)
  message.success(`${key} 已保存`)
}

async function refreshData() {
  await store.fetch()
  dirtySections.value.clear()
  message.success('已刷新')
}

watch(showPreview, async (val) => {
  if (val) {
    await store.fetchPreview()
  }
})

onMounted(() => {
  const bId = bookId.value
  if (bId) {
    store.setBookId(bId)
    if (!booksStore.currentBook) {
      booksStore.selectBook(bId).catch(() => {})
    }
  }
  store.fetch()
})
</script>

<style scoped>
.worldview-editor {
  max-width: 960px;
  margin: 0 auto;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.editor-header h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.section-tabs {
  min-height: 400px;
}

.section-content {
  padding-top: 16px;
}

.section-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--divider-color, #efefef);
}

.loading-center {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.preview-textarea {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font-mono, 'SF Mono', 'Fira Code', monospace);
  font-size: 13px;
  line-height: 1.7;
  color: var(--color-text);
  background: #f8f8f8;
  border-radius: 6px;
  padding: 16px;
  margin: 0;
}
</style>
