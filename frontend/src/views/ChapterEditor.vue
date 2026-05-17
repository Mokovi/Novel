<template>
  <div class="chapter-editor">
    <!-- Generating indicator bar -->
    <div v-if="generating" class="generating-bar" />

    <!-- Top bar -->
    <div class="top-bar">
      <h2 class="editor-title">章节编辑器</h2>
      <div class="top-actions">
        <n-button
          v-if="store.currentChapter"
          :disabled="generating"
          type="primary"
          @click="handleSave"
        >
          保存
        </n-button>
        <n-button
          v-if="store.currentChapter"
          :disabled="generating"
          @click="handleDownload"
        >
          下载
        </n-button>
        <n-popconfirm
          v-if="store.currentChapter"
          @positive-click="handleDelete"
        >
          <template #trigger>
            <n-button :disabled="generating" class="btn-delete">删除章节</n-button>
          </template>
          确定删除此章节？删除后不可恢复。
        </n-popconfirm>
      </div>
    </div>

    <!-- Three-column layout -->
    <n-layout has-sider class="editor-layout" position="absolute">
      <!-- Left: Chapter list -->
      <n-layout-sider width="220" bordered class="left-sider">
        <n-scrollbar style="height: 100%">
          <n-menu
            :value="String(store.currentChapter?.id)"
            :options="chapterMenuOptions"
            @update:value="onSelectChapter"
          />
        </n-scrollbar>
      </n-layout-sider>

      <!-- Center: Editor -->
      <n-layout-content class="center-content">
        <template v-if="store.currentChapter">
          <div v-if="generating" class="stream-container">
            <StreamOutput :content="streamContent" :streaming="true" />
          </div>
          <div v-else class="editor-container">
            <editor-content :editor="editor" class="editor-content" />
          </div>
        </template>
        <n-empty v-else description="从左侧选择或创建章节" class="empty-editor" />
      </n-layout-content>

      <!-- Right: Meta panel -->
      <n-layout-sider
        v-if="store.currentChapter"
        width="280"
        bordered
        position="right"
        class="right-sider"
      >
        <n-scrollbar style="height: 100%; padding: 16px">
          <n-space vertical :size="14">
            <n-form-item label="标题">
              <n-input v-model:value="editTitle" />
            </n-form-item>
            <n-form-item label="摘要">
              <n-input v-model:value="editSummary" type="textarea" rows="4" />
            </n-form-item>
            <n-divider />
            <n-form-item label="状态">
              <n-space>
                <n-tag :type="statusType(store.currentChapter.status)">
                  {{ statusLabel(store.currentChapter.status) }}
                </n-tag>
              </n-space>
            </n-form-item>
            <n-button
              size="large"
              block
              :type="generating ? 'warning' : 'primary'"
              :loading="generating"
              @click="handleGenerate"
              class="generate-btn"
            >
              {{ generating ? '生成中...' : store.currentChapter.content ? '重新生成' : 'AI 生成' }}
            </n-button>
            <n-form-item label="字数">
              <n-text>{{ editContent.length }} 字</n-text>
            </n-form-item>
            <n-divider />
            <n-text depth="3" class="meta-label">AI 生成</n-text>
          </n-space>
        </n-scrollbar>
      </n-layout-sider>
    </n-layout>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useChaptersStore } from '../stores/chapters.js'
import { updateChapter, deleteChapter, downloadChapter } from '../api/chapters.js'
import { generateChapter } from '../api/generate.js'
import StreamOutput from '../components/common/StreamOutput.vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'

const store = useChaptersStore()
const router = useRouter()
const route = useRoute()
const message = useMessage()

// Tiptap editor
const editor = useEditor({
  content: '',
  extensions: [
    StarterKit,
    Placeholder.configure({ placeholder: '在此编辑章节正文...' }),
  ],
  onUpdate: ({ editor }) => {
    editContent.value = editor.getText()
  },
})

// Generation state
const generating = ref(false)
const streamContent = ref('')
let abortController = null

// Edit buffers
const editTitle = ref('')
const editSummary = ref('')
const editContent = ref('')

// Chapter menu (grouped by volume)
const chapterMenuOptions = computed(() => {
  const options = []
  for (const vol of store.volumes) {
    const children = store.chapters
      .filter((c) => c.volume_id === vol.id)
      .map((c) => ({
        label: c.title,
        key: String(c.id),
      }))
    if (children.length) {
      options.push({
        label: vol.title,
        key: `vol-${vol.id}`,
        children,
      })
    }
  }
  return options
})

const statusType = (s) =>
  ({ pending: 'default', generating: 'warning', completed: 'success' }[s] || 'default')
const statusLabel = (s) =>
  ({ pending: '待生成', generating: '生成中', completed: '已完成' }[s] || s)

// Chapter selection
async function onSelectChapter(key) {
  const id = parseInt(key, 10)
  router.push(`/editor/${id}`)
}

// Watch route param
watch(
  () => route.params.id,
  async (id) => {
    if (id) {
      await store.selectChapter(parseInt(id, 10))
      syncEditBuffers()
      if (route.query.generate === '1') {
        router.replace({ path: route.path, params: route.params })
        handleGenerate()
      }
    }
  },
  { immediate: true },
)

function syncEditBuffers() {
  if (store.currentChapter) {
    editTitle.value = store.currentChapter.title || ''
    editSummary.value = store.currentChapter.summary || ''
    editContent.value = store.currentChapter.content || ''
    const content = store.currentChapter.content || ''
    if (content) {
      const html = content
        .split('\n\n')
        .map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`)
        .join('')
      editor.value?.commands.setContent(html)
    } else {
      editor.value?.commands.setContent('')
    }
  }
}

// Generate
async function handleGenerate() {
  if (!store.currentChapter) return
  if (store.currentChapter.content) {
    const ok = window.confirm('章节已有内容，重新生成将覆盖现有内容。确定继续？')
    if (!ok) return
  }

  generating.value = true
  streamContent.value = ''

  abortController = generateChapter(
    store.currentChapter.id,
    {
      onStart: () => {},
      onToken: (token) => {
        streamContent.value += token
      },
      onDone: async () => {
        generating.value = false
        message.success('生成完成')
        // Reload chapter to get saved content
        await store.selectChapter(store.currentChapter.id)
        syncEditBuffers()
      },
      onError: (msg) => {
        generating.value = false
        message.error(`生成失败: ${msg}`)
      },
    },
  )
}

// Save
async function handleSave() {
  if (!store.currentChapter) return
  try {
    await updateChapter(store.currentChapter.id, {
      title: editTitle.value,
      summary: editSummary.value,
      content: editContent.value,
    })
    message.success('已保存')
    await store.selectChapter(store.currentChapter.id)
  } catch (e) {
    message.error(`保存失败: ${e.response?.data?.detail || e.message}`)
  }
}

async function handleDownload() {
  if (!store.currentChapter) return
  const res = await downloadChapter(store.currentChapter.id)
  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = `${store.currentChapter.title || 'chapter'}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

async function handleDelete() {
  if (!store.currentChapter) return
  try {
    await deleteChapter(store.currentChapter.id)
    message.success('章节已删除')
    router.push('/outline')
  } catch (e) {
    message.error(`删除失败: ${e.response?.data?.detail || e.message}`)
  }
}

// Load data on mount
onMounted(async () => {
  await store.fetchVolumes()
  await store.fetchChapters()
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<style scoped>
.chapter-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Generating indicator bar */
.generating-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--color-accent) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  z-index: 10;
}

/* Top bar */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.editor-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-delete {
  --n-color: transparent !important;
  --n-color-hover: rgba(196, 90, 90, 0.08) !important;
  --n-text-color: var(--color-error) !important;
  --n-border: 1px solid var(--color-error) !important;
}

/* Editor layout */
.editor-layout {
  height: calc(100vh - 140px) !important;
  position: relative !important;
}

.left-sider {
  background: var(--color-bg-card);
}

.center-content {
  padding: 0;
  display: flex;
  flex-direction: column;
}

.stream-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Tiptap editor */
:deep(.tiptap-wrapper) {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--color-bg-editor);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

:deep(.tiptap-content) {
  min-height: 400px;
  outline: none;
  font-family: var(--font-editor);
  font-size: 16px;
  line-height: 1.9;
  color: var(--color-text-primary);
}

:deep(.tiptap-content p) {
  margin: 0 0 0.6em;
}

:deep(.tiptap-content .ProseMirror) {
  min-height: 400px;
  padding: 0;
  outline: none;
}

:deep(.ProseMirror p.is-editor-empty:first-child::before) {
  color: var(--color-text-muted);
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* Right sider */
.right-sider {
  background: var(--color-bg-card);
}

.generate-btn {
  margin: 8px 0;
  font-weight: 600;
  font-size: 15px;
}

.meta-label {
  font-size: 12px;
}

.empty-editor {
  margin-top: 80px;
}
</style>
