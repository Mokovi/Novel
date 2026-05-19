<template>
  <div class="scriptorium">
    <!-- ==================== EMPTY STATE ==================== -->
    <div v-if="!store.currentChapter" class="scriptorium-empty">
      <div class="empty-emblem">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <path d="M12 40V8h16l8 8v24H12z" stroke="#c9a94e" stroke-width="1.5" fill="none"/>
          <path d="M28 8v8h8" stroke="#c9a94e" stroke-width="1.5" fill="none"/>
          <path d="M18 22h12M18 28h8M18 34h10" stroke="#b5a99a" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <h2 class="empty-heading">选择章节开始写作</h2>
        <p class="empty-desc">从左侧目录中选择一个章节，或前往大纲视图创建新章节</p>
        <button class="empty-action" @click="goToOutline">前往大纲</button>
      </div>
    </div>

    <!-- ==================== MAIN LAYOUT ==================== -->
    <template v-else>
      <!-- ─── TOP BAR ─── -->
      <header class="scriptorium-topbar">
        <div class="topbar-left">
          <button class="topbar-back" @click="goToOutline" title="返回大纲">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M11 4L6 9l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>大纲</span>
          </button>
          <div class="topbar-divider" />
          <div class="topbar-title-area">
            <input
              v-model="editTitle"
              class="topbar-title-input"
              placeholder="无标题章节"
              @blur="handleSave"
            />
          </div>
        </div>

        <div class="topbar-right">
          <span class="topbar-wordcount">{{ editContent.length }} 字</span>
          <div class="topbar-divider" />
          <button
            class="tb-btn tb-save"
            :class="{ dirty: isDirty }"
            @click="handleSave"
            title="保存"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 2h7l3 3v9H3V2z" stroke="currentColor" stroke-width="1.3" fill="none"/>
              <path d="M5 2v4h5V2" stroke="currentColor" stroke-width="1.3" fill="none"/>
              <circle cx="8" cy="11" r="1.5" stroke="currentColor" stroke-width="1.3" fill="none"/>
            </svg>
            <span>保存</span>
          </button>
          <button
            class="tb-btn tb-generate"
            :class="{ generating: genPhase === 'generating' }"
            :disabled="genPhase === 'generating'"
            @click="handleGenerate"
          >
            <svg v-if="genPhase !== 'generating'" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.3"/>
            </svg>
            <span v-else class="tb-generating-dots">
              <span /><span /><span />
            </span>
            <span>{{ genPhase === 'generating' ? '生成中' : (store.currentChapter?.content ? '重新生成' : 'AI 生成') }}</span>
          </button>
          <button
            class="tb-btn tb-inspector-toggle"
            :class="{ active: inspectorOpen }"
            @click="inspectorOpen = !inspectorOpen"
            title="属性面板"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.3" fill="none"/>
              <rect x="9" y="1" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.3" fill="none"/>
              <rect x="1" y="9" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.3" fill="none"/>
              <rect x="9" y="9" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.3" fill="none"/>
            </svg>
          </button>
        </div>
      </header>

      <!-- ─── BODY ─── -->
      <div class="scriptorium-body">
        <!-- Left: TOC -->
        <aside class="toc-rail" :class="{ collapsed: tocCollapsed }">
          <div class="toc-header">
            <span v-if="!tocCollapsed" class="toc-label">目录</span>
            <button class="toc-collapse-btn" @click="tocCollapsed = !tocCollapsed" :title="tocCollapsed ? '展开' : '折叠'">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path v-if="!tocCollapsed" d="M7 3L4 6l3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path v-else d="M5 3l3 3-3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
          <div v-if="!tocCollapsed" class="toc-scroll">
            <div
              v-for="vol in store.volumes"
              :key="vol.id"
              class="toc-volume"
            >
              <div class="toc-volume-title">
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <rect x="1" y="1" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.2" fill="none"/>
                </svg>
                <span>{{ vol.title }}</span>
              </div>
              <div
                v-for="ch in chaptersInVolume(vol.id)"
                :key="ch.id"
                class="toc-entry"
                :class="{
                  active: ch.id === store.currentChapter?.id,
                  'status-completed': ch.status === 'completed',
                  'status-generating': ch.status === 'generating',
                }"
                @click="onSelectChapter(ch.id)"
              >
                <span class="toc-entry-indicator" />
                <span class="toc-entry-title">{{ ch.title }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- Center: Editor -->
        <main class="editor-zone">
          <!-- Prompt panel (Phase: idle) -->
          <div v-if="genPhase === 'idle'" class="gen-prompt-panel">
            <div class="gen-prompt-card">
              <h3 class="gen-prompt-title">{{ store.currentChapter?.content ? '重新生成章节' : 'AI 生成章节' }}</h3>
              <p class="gen-prompt-desc">输入补充提示词（可选），或直接点击"开始生成"</p>
              <textarea
                v-model="userPrompt"
                class="gen-prompt-textarea"
                placeholder="补充提示词（可选）：输入您对本章节内容的特定要求..."
                rows="4"
              />
              <div class="gen-prompt-actions">
                <button class="gen-btn gen-btn-cancel" @click="cancelGeneration">取消</button>
                <button class="gen-btn gen-btn-start" @click="startGeneration">开始生成</button>
              </div>
            </div>
          </div>

          <!-- Generating overlay (Phase: generating) -->
          <div v-else-if="genPhase === 'generating'" class="gen-overlay">
            <div class="gen-bar" />
            <div class="gen-stream">
              <div class="gen-stream-header">
                <span class="gen-stream-dot" />
                <span>AI 正在创作...</span>
              </div>
              <StreamOutput :content="streamContent" :streaming="true" />
              <div class="gen-stream-footer">
                <button class="gen-btn gen-btn-cancel gen-btn-sm" @click="cancelGeneration">取消</button>
              </div>
            </div>
          </div>

          <!-- Done overlay (Phase: done) -->
          <div v-else-if="genPhase === 'done'" class="gen-overlay">
            <div class="gen-bar gen-bar-done" />
            <div class="gen-stream">
              <div class="gen-stream-header">
                <span class="gen-stream-dot gen-stream-dot-done" />
                <span>生成完成</span>
              </div>
              <StreamOutput :content="streamContent" :streaming="false" />
              <div class="gen-stream-footer">
                <button class="gen-btn gen-btn-start gen-btn-sm" @click="closeGenPanel">关闭</button>
              </div>
            </div>
          </div>

          <!-- Paper editor (no gen phase active) -->
          <div v-show="!genPhase" class="paper-wrap">
            <div class="paper">
              <editor-content :editor="editor" class="paper-editor" />
            </div>
          </div>

          <!-- Download floating button -->
          <button v-if="!genPhase && store.currentChapter?.content" class="fab-download" @click="handleDownload" title="下载为 TXT">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 10v3h10v-3M8 2v8M5 7l3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </main>

        <!-- Right: Inspector -->
        <aside class="inspector-rail" :class="{ open: inspectorOpen }">
          <div class="inspector-scroll">
            <!-- Section: Status -->
            <div class="is-section is-status">
              <span class="status-badge" :class="store.currentChapter.status">
                <span class="status-dot" />
                {{ statusLabel(store.currentChapter.status) }}
              </span>
              <button class="is-delete-btn" @click="showDeleteConfirm = true">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M2 3.5h10M5 3.5V2a.5.5 0 01.5-.5h3A.5.5 0 019 2v1.5M11 3.5v8a1 1 0 01-1 1H4a1 1 0 01-1-1v-8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>

            <!-- Section: Summary -->
            <div class="is-section">
              <button class="is-section-header" @click="expandedSections.summary = !expandedSections.summary">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M4 9l3-3-3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" :class="{ rotated: expandedSections.summary }" class="is-chevron"/>
                </svg>
                <span>摘要</span>
              </button>
              <div v-show="expandedSections.summary" class="is-section-body">
                <textarea
                  v-model="editSummary"
                  class="is-textarea"
                  rows="3"
                  placeholder="章节摘要..."
                  @blur="handleSave"
                />
              </div>
            </div>

            <!-- Section: AI Summary -->
            <div class="is-section">
              <button class="is-section-header" @click="expandedSections.aiSummary = !expandedSections.aiSummary">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M4 9l3-3-3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" :class="{ rotated: expandedSections.aiSummary }" class="is-chevron"/>
                </svg>
                <span>AI 摘要</span>
                <button
                  v-if="store.currentChapter?.content"
                  class="is-regenerate-btn"
                  title="重新生成摘要"
                  @click.stop="handleRegenerateSummary"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M1 2v4h4M11 10V6H7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </button>
              <div v-show="expandedSections.aiSummary" class="is-section-body">
                <textarea
                  v-model="editAiSummary"
                  class="is-textarea"
                  rows="3"
                  placeholder="AI 生成后自动填充..."
                  @blur="handleSaveAiSummary"
                />
              </div>
            </div>

            <!-- Section: Generation -->
            <div class="is-section">
              <button class="is-section-header" @click="expandedSections.gen = !expandedSections.gen">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M4 9l3-3-3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" :class="{ rotated: expandedSections.gen }" class="is-chevron"/>
                </svg>
                <span>生成设置</span>
              </button>
              <div v-show="expandedSections.gen" class="is-section-body">
                <!-- Worldview level -->
                <div class="is-field">
                  <span class="is-field-label">世界观注入</span>
                  <div class="is-radio-row">
                    <button
                      v-for="opt in worldviewOptions"
                      :key="opt.value"
                      class="is-radio"
                      :class="{ active: editingWorldviewLevel === opt.value }"
                      @click="handleWorldviewLevelChange(opt.value)"
                    >{{ opt.label }}</button>
                  </div>
                </div>

                <!-- Character association -->
                <div class="is-field">
                  <span class="is-field-label">关联人物</span>
                  <n-select
                    multiple
                    filterable
                    placeholder="搜索人物..."
                    :options="characterOptions"
                    v-model:value="editingCharacterIds"
                    @update:value="handleCharacterChange"
                    :loading="charactersLoading"
                    size="small"
                  />
                </div>
                <div v-if="chapterCharacters.length" class="is-chips">
                  <span
                    v-for="ch in chapterCharacters"
                    :key="ch.id"
                    class="is-chip"
                    :class="ch.role_type"
                  >
                    {{ ch.name }}
                    <button class="is-chip-remove" @click="removeCharacter(ch.id)">✕</button>
                  </span>
                </div>

                <!-- Admin preview -->
                <div v-if="adminStore.isAdmin" class="is-field" style="margin-top:12px">
                  <button class="is-preview-btn" @click="handlePreviewPrompt">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                    </svg>
                    提示词预览
                  </button>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <!-- Delete confirmation dialog -->
        <div v-if="showDeleteConfirm" class="delete-overlay" @click.self="showDeleteConfirm = false">
          <div class="delete-dialog">
            <h3 class="delete-dialog-title">删除章节</h3>
            <p class="delete-dialog-desc">确定删除此章节？删除后不可恢复。</p>
            <div class="delete-dialog-actions">
              <button class="dd-btn dd-cancel" @click="showDeleteConfirm = false">取消</button>
              <button class="dd-btn dd-confirm" @click="handleDelete">删除</button>
            </div>
          </div>
        </div>

        <!-- Regenerate confirmation modal -->
        <n-modal v-model:show="showRegenerateConfirm" preset="dialog" title="重新生成章节" content="章节已有内容，重新生成将覆盖现有内容。确定继续？" positive-text="确定继续" negative-text="取消" @positive-click="confirmRegenerate" @negative-click="showRegenerateConfirm = false" />
      </div>
    </template>

    <!-- Prompt preview modal -->
    <n-modal v-model:show="showPreviewModal" preset="card" title="提示词预览" style="max-width: 800px">
      <n-space v-if="previewLoading" justify="center">
        <n-spin />
      </n-space>
      <n-space v-else-if="previewData" vertical :size="12">
        <n-space>
          <n-tag type="info" size="small">模型: {{ previewData.model }}</n-tag>
          <n-tag size="small">模板: {{ previewData.template_name }}</n-tag>
          <n-tag size="small">预估: ~{{ previewData.token_estimate }} tokens</n-tag>
        </n-space>
        <n-input
          type="textarea"
          :value="previewData.prompt"
          readonly
          rows="20"
          class="preview-textarea"
        />
      </n-space>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useChaptersStore } from '../stores/chapters.js'
import { updateChapter, deleteChapter, downloadChapter, getChapterCharacters, setChapterCharacters } from '../api/chapters.js'
import { listCharacters } from '../api/characters.js'
import { generateChapter, previewPrompt, regenerateSummary } from '../api/generate.js'
import { useAdminStore } from '../stores/admin.js'
import StreamOutput from '../components/common/StreamOutput.vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'

const store = useChaptersStore()
const adminStore = useAdminStore()
const router = useRouter()
const route = useRoute()
const message = useMessage()

// ── Editor ──
const editor = useEditor({
  content: '',
  extensions: [
    StarterKit,
    Placeholder.configure({ placeholder: '在此开始写作...' }),
  ],
  onUpdate: ({ editor }) => {
    editContent.value = editor.getText()
    isDirty.value = true
  },
})

// ── State ──
const genPhase = ref(null) // null | 'idle' | 'generating' | 'done'
const streamContent = ref('')
const userPrompt = ref('')
let abortController = null

const showPreviewModal = ref(false)
const previewData = ref(null)
const previewLoading = ref(false)

const editTitle = ref('')
const editSummary = ref('')
const editAiSummary = ref('')
const editContent = ref('')
const isDirty = ref(false)

const allCharacters = ref([])
const chapterCharacters = ref([])
const editingCharacterIds = ref([])
const charactersLoading = ref(false)

const editingWorldviewLevel = ref('medium')
const inspectorOpen = ref(false)
const tocCollapsed = ref(false)
const showDeleteConfirm = ref(false)

const expandedSections = ref({
  summary: true,
  aiSummary: false,
  gen: true,
})

const worldviewOptions = [
  { label: '精简', value: 'low' },
  { label: '标准', value: 'medium' },
  { label: '详细', value: 'high' },
]

const characterOptions = computed(() =>
  allCharacters.value.map((c) => ({
    label: `${c.name}${c.role_type ? ` (${c.role_type})` : ''}`,
    value: c.id,
  }))
)

// ── Computed ──
const chaptersInVolume = (volId) => store.chapters.filter(c => c.volume_id === volId)

const statusType = (s) =>
  ({ pending: 'default', generating: 'warning', completed: 'success' }[s] || 'default')
const statusLabel = (s) =>
  ({ pending: '待生成', generating: '生成中', completed: '已完成' }[s] || s)

// ── Navigation ──
const bookId = computed(() => Number(route.params.bookId))

function goToOutline() {
  router.push(`/books/${bookId.value}/outline`)
}

function onSelectChapter(id) {
  router.push(`/books/${bookId.value}/editor/${id}`)
}

watch(
  () => route.params.id,
  async (id) => {
    if (id) {
      await store.selectChapter(parseInt(id, 10))
      syncEditBuffers()
      if (route.query.generate === '1') {
        router.replace({ path: route.path, params: route.params })
        // Trigger the prompt panel; user must click "开始生成" to proceed
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
    editAiSummary.value = store.currentChapter.ai_summary || ''
    editContent.value = store.currentChapter.content || ''
    editingWorldviewLevel.value = store.currentChapter.worldview_level || 'medium'
    isDirty.value = false
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
    loadChapterCharacters()
  }
}

// ── Characters ──
async function loadChapterCharacters() {
  if (!store.currentChapter) return
  try {
    const res = await getChapterCharacters(store.currentChapter.id)
    chapterCharacters.value = res.data
    editingCharacterIds.value = res.data.map((c) => c.id)
  } catch (e) {
    console.error('Failed to load chapter characters:', e)
  }
}

async function handleCharacterChange(ids) {
  if (!store.currentChapter) return
  editingCharacterIds.value = ids
  try {
    const res = await setChapterCharacters(store.currentChapter.id, ids)
    chapterCharacters.value = res.data
  } catch (e) {
    message.error(`保存人物关联失败: ${e.response?.data?.detail || e.message}`)
  }
}

function removeCharacter(id) {
  handleCharacterChange(editingCharacterIds.value.filter(v => v !== id))
}

// ── Worldview level ──
async function handleWorldviewLevelChange(val) {
  if (!store.currentChapter) return
  editingWorldviewLevel.value = val
  try {
    await updateChapter(store.currentChapter.id, { worldview_level: val })
    store.currentChapter.worldview_level = val
    message.success('世界观级别已更新')
  } catch (e) {
    message.error(`更新失败: ${e.response?.data?.detail || e.message}`)
  }
}

// ── AI Generation ──
function handleGenerate() {
  if (!store.currentChapter) return
  if (store.currentChapter.content) {
    showRegenerateConfirm.value = true
    return
  }
  openGenPanel()
}

const showRegenerateConfirm = ref(false)

function confirmRegenerate() {
  showRegenerateConfirm.value = false
  openGenPanel()
}

function openGenPanel() {
  genPhase.value = 'idle'
  userPrompt.value = ''
  streamContent.value = ''
}

function startGeneration() {
  if (!store.currentChapter) return
  genPhase.value = 'generating'
  streamContent.value = ''

  abortController = generateChapter(
    store.currentChapter.id,
    {
      onStart: () => {},
      onToken: (token) => {
        streamContent.value += token
      },
      onSummary: (summary) => {
        editAiSummary.value = summary
      },
      onDone: async () => {
        genPhase.value = 'done'
        message.success('生成完成')
        await store.selectChapter(store.currentChapter.id)
        syncEditBuffers()
      },
      onError: (msg) => {
        genPhase.value = 'done'
        message.error(`生成失败: ${msg}`)
      },
    },
    { user_prompt: userPrompt.value },
  )
}

function cancelGeneration() {
  abortController?.abort()
  genPhase.value = null
  streamContent.value = ''
  userPrompt.value = ''
}

function closeGenPanel() {
  genPhase.value = null
  streamContent.value = ''
  userPrompt.value = ''
}

async function handleSaveAiSummary() {
  if (!store.currentChapter) return
  try {
    await updateChapter(store.currentChapter.id, { ai_summary: editAiSummary.value })
  } catch (e) {
    console.error('Failed to save AI summary:', e)
  }
}

async function handleRegenerateSummary() {
  if (!store.currentChapter?.content) {
    message.warning('章节暂无内容，无法生成摘要')
    return
  }
  try {
    const res = await regenerateSummary(store.currentChapter.id)
    editAiSummary.value = res.summary
    message.success('摘要已重新生成')
  } catch (e) {
    message.error(`摘要生成失败: ${e.message}`)
  }
}

async function handlePreviewPrompt() {
  if (!store.currentChapter) return
  previewLoading.value = true
  showPreviewModal.value = true
  try {
    const res = await previewPrompt(store.currentChapter.id, bookId.value)
    previewData.value = res.data
  } catch (e) {
    message.error(`获取预览失败: ${e.message}`)
    showPreviewModal.value = false
  } finally {
    previewLoading.value = false
  }
}

// ── Save ──
async function handleSave() {
  if (!store.currentChapter) return
  try {
    await updateChapter(store.currentChapter.id, {
      title: editTitle.value,
      summary: editSummary.value,
      content: editContent.value,
      worldview_level: editingWorldviewLevel.value,
    })
    isDirty.value = false
    message.success('已保存')
    await store.selectChapter(store.currentChapter.id)
  } catch (e) {
    message.error(`保存失败: ${e.response?.data?.detail || e.message}`)
  }
}

// ── Download ──
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

// ── Delete ──
async function handleDelete() {
  if (!store.currentChapter) return
  showDeleteConfirm.value = false
  try {
    await deleteChapter(store.currentChapter.id)
    message.success('章节已删除')
    router.push(`/books/${bookId.value}/outline`)
  } catch (e) {
    message.error(`删除失败: ${e.response?.data?.detail || e.message}`)
  }
}

// ── Lifecycle ──
onMounted(async () => {
  await store.fetchVolumes(bookId.value)
  await store.fetchChapters(bookId.value)
  try {
    charactersLoading.value = true
    const res = await listCharacters(bookId.value, { limit: 500 })
    allCharacters.value = res.data
  } catch (e) {
    console.error('Failed to load characters:', e)
  } finally {
    charactersLoading.value = false
  }
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<style scoped>
/* ==============================
   SCRIPTORIUM — Base Layout
   ============================== */
.scriptorium {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
  position: relative;
}

/* ── Empty State ── */
.scriptorium-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-emblem {
  text-align: center;
  animation: fade-in-up 0.5s ease both;
}

.empty-emblem svg {
  margin: 0 auto 20px;
  display: block;
}

.empty-heading {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 24px;
}

.empty-action {
  padding: 10px 24px;
  border: 1px solid var(--color-accent);
  background: transparent;
  color: var(--color-accent-dark);
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  font-family: var(--font-ui);
  transition: all var(--transition-fast);
}
.empty-action:hover {
  background: var(--color-accent);
  color: #fff;
}

/* ==============================
   TOP BAR
   ============================== */
.scriptorium-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 20px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border-light);
  position: relative;
  z-index: 20;
}

.topbar-left,
.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-back {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-family: var(--font-ui);
  cursor: pointer;
  border-radius: 4px;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.topbar-back:hover {
  color: var(--color-text-primary);
  background: rgba(0,0,0,0.04);
}

.topbar-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border);
  flex-shrink: 0;
}

.topbar-title-area {
  display: flex;
  align-items: center;
}

.topbar-title-input {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
  background: transparent;
  border: none;
  outline: none;
  padding: 4px 8px;
  border-radius: 4px;
  min-width: 200px;
  transition: background var(--transition-fast);
}
.topbar-title-input:hover { background: rgba(0,0,0,0.03); }
.topbar-title-input:focus { background: rgba(201, 169, 78, 0.08); }

.topbar-wordcount {
  font-size: 12px;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* Top bar buttons */
.tb-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-text-secondary);
  border-radius: 6px;
  font-size: 13px;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.tb-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
}

.tb-save.dirty {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
  background: rgba(201, 169, 78, 0.06);
}

.tb-generate {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}
.tb-generate:hover:not(:disabled) {
  background: var(--color-accent-light);
  border-color: var(--color-accent-light);
  color: #fff;
}
.tb-generate:disabled { opacity: 0.6; cursor: not-allowed; }
.tb-generate.generating {
  background: var(--color-text-secondary);
  border-color: var(--color-text-secondary);
}

.tb-generating-dots {
  display: flex;
  gap: 3px;
}
.tb-generating-dots span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #fff;
  animation: pulse-dot 1.2s ease-in-out infinite;
}
.tb-generating-dots span:nth-child(2) { animation-delay: 0.2s; }
.tb-generating-dots span:nth-child(3) { animation-delay: 0.4s; }

.tb-inspector-toggle {
  padding: 7px 9px;
}
.tb-inspector-toggle.active {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
  background: rgba(201, 169, 78, 0.08);
}

/* ==============================
   BODY LAYOUT
   ============================== */
.scriptorium-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

/* ==============================
   TOC RAIL (Left)
   ============================== */
.toc-rail {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-right: 1px solid var(--color-border-light);
  transition: width var(--transition-base);
  overflow: hidden;
}
.toc-rail.collapsed {
  width: 40px;
}

.toc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px 8px;
  flex-shrink: 0;
}

.toc-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 1.5px;
}

.toc-collapse-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 3px;
  transition: all var(--transition-fast);
}
.toc-collapse-btn:hover {
  color: var(--color-text-primary);
  background: rgba(0,0,0,0.04);
}

.toc-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 16px;
}

.toc-volume {
  margin-bottom: 12px;
}

.toc-volume-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  padding: 6px 8px 4px;
  letter-spacing: 0.5px;
}

.toc-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 8px 7px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
  position: relative;
}
.toc-entry:hover {
  background: rgba(0,0,0,0.03);
  color: var(--color-text-primary);
}
.toc-entry.active {
  background: rgba(201, 169, 78, 0.1);
  color: var(--color-accent-dark);
}
.toc-entry.active .toc-entry-indicator {
  background: var(--color-accent);
}

.toc-entry-indicator {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-border);
  flex-shrink: 0;
  transition: background var(--transition-fast);
}
.toc-entry.status-completed .toc-entry-indicator {
  background: var(--color-success);
}
.toc-entry.status-generating .toc-entry-indicator {
  background: var(--color-warning);
}

.toc-entry-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ==============================
   EDITOR ZONE (Center)
   ============================== */
.editor-zone {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
  position: relative;
  overflow: hidden;
}

.paper-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 32px 48px;
  background:
    radial-gradient(ellipse at 50% 0%, rgba(201, 169, 78, 0.04) 0%, transparent 60%),
    var(--color-bg-page);
}

.paper {
  flex: 1 0 auto;
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  background: var(--color-bg-editor);
  border-radius: var(--radius-lg);
  box-shadow:
    0 1px 3px rgba(0,0,0,0.04),
    0 4px 16px rgba(0,0,0,0.04),
    0 0 0 1px rgba(0,0,0,0.02);
  padding: 48px 56px;
  min-height: 400px;
  position: relative;
}

.paper::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: var(--radius-lg);
  background:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 27px,
      rgba(201, 169, 78, 0.03) 27px,
      rgba(201, 169, 78, 0.03) 28px
    );
  pointer-events: none;
}

.paper-editor {
  min-height: 400px;
  outline: none;
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 100%;
}

:deep(.ProseMirror) {
  min-height: 400px;
  outline: none;
  font-family: var(--font-editor);
  font-size: 17px;
  line-height: 2;
  color: var(--color-text-primary);
  letter-spacing: 0.01em;
  word-break: break-word;
  overflow-wrap: break-word;
}

:deep(.ProseMirror p) {
  margin: 0 0 0.5em;
  text-indent: 2em;
}

:deep(.ProseMirror p.is-editor-empty:first-child::before) {
  color: var(--color-text-muted);
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
  opacity: 0.5;
}

/* FAB download */
.fab-download {
  position: absolute;
  bottom: 24px;
  right: 24px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
  z-index: 10;
}
.fab-download:hover {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

/* ==============================
   GENERATING OVERLAY + PROMPT PANEL
   ============================== */
.gen-prompt-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background: var(--color-bg-page);
}

.gen-prompt-card {
  max-width: 520px;
  width: 100%;
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 32px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.04);
  border: 1px solid var(--color-border-light);
}

.gen-prompt-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 6px;
}

.gen-prompt-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 16px;
}

.gen-prompt-textarea {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 12px 14px;
  font-size: 14px;
  font-family: var(--font-ui);
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  resize: vertical;
  outline: none;
  transition: border-color var(--transition-fast);
  line-height: 1.6;
  box-sizing: border-box;
}
.gen-prompt-textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px rgba(201, 169, 78, 0.12);
}

.gen-prompt-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.gen-btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid var(--color-border);
}

.gen-btn-sm {
  padding: 6px 14px;
  font-size: 12px;
}

.gen-btn-cancel {
  background: #fff;
  color: var(--color-text-secondary);
}
.gen-btn-cancel:hover {
  border-color: var(--color-text-muted);
  color: var(--color-text-primary);
}

.gen-btn-start {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}
.gen-btn-start:hover {
  background: var(--color-accent-light);
  border-color: var(--color-accent-light);
}

.gen-stream-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  flex-shrink: 0;
}

.gen-bar-done {
  background: linear-gradient(90deg, transparent, var(--color-success), transparent);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.gen-stream-dot-done {
  background: var(--color-success);
  animation: none;
}

.gen-overlay {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.gen-bar {
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-accent), transparent);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  flex-shrink: 0;
}

.gen-stream {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px 32px;
  overflow: hidden;
}

.gen-stream-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 16px;
  flex-shrink: 0;
}

.gen-stream-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-accent);
  animation: pulse-amber 1.5s ease-in-out infinite;
}

.gen-stream > :deep(.stream-output) {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-editor);
  overflow-y: auto;
}

/* ==============================
   INSPECTOR RAIL (Right)
   ============================== */
.inspector-rail {
  width: 0;
  overflow: hidden;
  background: #fff;
  border-left: 1px solid var(--color-border-light);
  transition: width var(--transition-base);
  flex-shrink: 0;
}
.inspector-rail.open {
  width: 280px;
}

.inspector-scroll {
  width: 280px;
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}

/* Status section */
.is-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background: var(--color-bg-page);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}
.status-badge .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-muted);
}
.status-badge.pending .status-dot { background: var(--color-text-muted); }
.status-badge.generating .status-dot { background: var(--color-warning); }
.status-badge.completed .status-dot { background: var(--color-success); }
.status-badge.pending { border-color: var(--color-border); color: var(--color-text-muted); }
.status-badge.generating { border-color: var(--color-warning); color: #b8860b; }
.status-badge.completed { border-color: var(--color-success); color: var(--color-success); }

.is-delete-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}
.is-delete-btn:hover {
  color: var(--color-error);
  background: rgba(196, 90, 90, 0.08);
}

/* Collapsible sections */
.is-section {
  margin-bottom: 4px;
}
.is-section + .is-section {
  border-top: 1px solid var(--color-border-light);
  padding-top: 4px;
}

.is-section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 10px 0;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-family: var(--font-ui);
  transition: color var(--transition-fast);
}
.is-section-header:hover {
  color: var(--color-text-primary);
}

.is-chevron {
  transition: transform var(--transition-fast);
}
.is-chevron.rotated {
  transform: rotate(90deg);
}

.is-section-body {
  padding: 4px 0 12px 18px;
}

.is-textarea {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 8px 10px;
  font-size: 13px;
  font-family: var(--font-ui);
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  resize: vertical;
  outline: none;
  transition: border-color var(--transition-fast);
  line-height: 1.5;
}
.is-textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px rgba(201, 169, 78, 0.12);
}
.is-textarea::placeholder {
  color: var(--color-text-muted);
  opacity: 0.6;
}

/* Fields */
.is-field {
  margin-bottom: 12px;
}
.is-field-label {
  display: block;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.is-radio-row {
  display: flex;
  gap: 2px;
  background: var(--color-bg-page);
  border-radius: 4px;
  padding: 2px;
  border: 1px solid var(--color-border);
}

.is-radio {
  flex: 1;
  padding: 5px 8px;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-family: var(--font-ui);
  cursor: pointer;
  border-radius: 3px;
  transition: all var(--transition-fast);
}
.is-radio.active {
  background: #fff;
  color: var(--color-accent-dark);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.is-radio:hover:not(.active) {
  color: var(--color-text-primary);
}

/* Character chips */
.is-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.is-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  background: var(--color-bg-page);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}
.is-chip.protagonist { border-color: var(--color-success); color: var(--color-success); }
.is-chip.antagonist { border-color: var(--color-error); color: var(--color-error); }
.is-chip.supporting { border-color: var(--color-info); color: var(--color-info); }

.is-chip-remove {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 10px;
  color: inherit;
  opacity: 0.5;
  transition: opacity var(--transition-fast);
  line-height: 1;
}
.is-chip-remove:hover { opacity: 1; }

.is-regenerate-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: auto;
  padding: 3px 6px;
  background: none;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  border-radius: 4px;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.is-regenerate-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
  background: rgba(201, 169, 78, 0.06);
}

.is-preview-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px 12px;
  background: rgba(230, 162, 60, 0.06);
  border: 1px dashed var(--color-warning, #e6a23c);
  color: var(--color-warning, #e6a23c);
  font-size: 12px;
  font-family: var(--font-ui);
  cursor: pointer;
  border-radius: 4px;
  transition: all var(--transition-fast);
}
.is-preview-btn:hover {
  background: var(--color-warning, #e6a23c);
  color: #fff;
}

/* ==============================
   DELETE DIALOG
   ============================== */
.delete-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  animation: fade-in 0.15s ease;
}

.delete-dialog {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 28px 32px 24px;
  max-width: 380px;
  width: 90%;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}

.delete-dialog-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.delete-dialog-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 24px;
  line-height: 1.5;
}

.delete-dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.dd-btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.dd-cancel {
  background: #fff;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}
.dd-cancel:hover {
  border-color: var(--color-text-muted);
}

.dd-confirm {
  background: var(--color-error);
  border: 1px solid var(--color-error);
  color: #fff;
}
.dd-confirm:hover {
  background: #d06a6a;
  border-color: #d06a6a;
}

/* Preview modal textarea */
.preview-textarea :deep(textarea) {
  font-family: monospace;
}

/* ==============================
   ANIMATIONS
   ============================== */
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes pulse-dot {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}
</style>
