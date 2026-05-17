<template>
  <n-space vertical :size="12" style="height: 100%">
    <!-- Top bar -->
    <n-space justify="space-between" align="center">
      <n-h2 style="margin: 0">章节编辑器</n-h2>
      <n-space>
        <n-button
          v-if="store.currentChapter"
          :disabled="generating"
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
            <n-button type="error" :disabled="generating">删除章节</n-button>
          </template>
          确定删除此章节？删除后不可恢复。
        </n-popconfirm>
      </n-space>
    </n-space>

    <!-- Three-column layout -->
    <n-layout has-sider style="height: calc(100vh - 140px)" position="absolute">
      <!-- Left: Chapter list -->
      <n-layout-sider width="220" bordered>
        <n-scrollbar style="height: 100%">
          <n-menu
            :value="String(store.currentChapter?.id)"
            :options="chapterMenuOptions"
            @update:value="onSelectChapter"
          />
        </n-scrollbar>
      </n-layout-sider>

      <!-- Center: Editor -->
      <n-layout-content style="padding: 12px">
        <template v-if="store.currentChapter">
          <div v-if="generating" style="height: 100%; display: flex; flex-direction: column;">
            <StreamOutput :content="streamContent" :streaming="true" />
          </div>
          <div v-else style="height: 100%; display: flex; flex-direction: column;">
            <div class="editor-toolbar">
              <n-space>
                <n-button size="tiny" @click="toggleBold">粗体</n-button>
                <n-button size="tiny" @click="toggleItalic">斜体</n-button>
                <n-button size="tiny" @click="toggleHeading">标题</n-button>
              </n-space>
            </div>
            <div class="tiptap-wrapper">
              <editor-content :editor="editor" class="tiptap-content" />
            </div>
          </div>
        </template>
        <n-empty v-else description="从左侧选择或创建章节" style="margin-top: 80px" />
      </n-layout-content>

      <!-- Right: Meta panel -->
      <n-layout-sider v-if="store.currentChapter" width="280" bordered position="right">
        <n-scrollbar style="height: 100%; padding: 12px">
          <n-space vertical>
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
                <n-button
                  size="small"
                  :type="generating ? 'warning' : 'primary'"
                  :loading="generating"
                  @click="handleGenerate"
                >
                  {{ generating ? '生成中...' : store.currentChapter.content ? '重新生成' : '生成' }}
                </n-button>
              </n-space>
            </n-form-item>
            <n-form-item label="字数">
              <n-text>{{ editContent.length }} 字</n-text>
            </n-form-item>
            <n-divider />
            <n-text depth="3" class="meta-label">生成参数（可选覆盖）</n-text>
            <n-form-item label="Temperature">
              <n-input-number v-model:value="overrideTemp" :min="0" :max="2" :step="0.1" placeholder="默认" />
            </n-form-item>
            <n-form-item label="Max Tokens">
              <n-input-number v-model:value="overrideMaxTokens" :min="1" :step="256" placeholder="默认" />
            </n-form-item>
          </n-space>
        </n-scrollbar>
      </n-layout-sider>
    </n-layout>
  </n-space>
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
const overrideTemp = ref(null)
const overrideMaxTokens = ref(null)

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

  const overrides = {}
  if (overrideTemp.value !== null) overrides.temperature = overrideTemp.value
  if (overrideMaxTokens.value !== null) overrides.max_tokens = overrideMaxTokens.value

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
    overrides,
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

// Tiptap toolbar actions
function toggleBold() {
  editor.value?.chain().focus().toggleBold().run()
}
function toggleItalic() {
  editor.value?.chain().focus().toggleItalic().run()
}
function toggleHeading() {
  editor.value?.chain().focus().toggleHeading({ level: 3 }).run()
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
.editor-toolbar {
  border-bottom: 1px solid #e0e0e0;
  padding: 8px;
  flex-shrink: 0;
}
.tiptap-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.tiptap-content {
  min-height: 300px;
  outline: none;
}
.tiptap-content :deep(p) {
  margin: 0 0 0.5em;
  line-height: 1.7;
}
.tiptap-content :deep(.ProseMirror) {
  min-height: 300px;
}
.meta-label {
  font-size: 12px;
}
</style>
