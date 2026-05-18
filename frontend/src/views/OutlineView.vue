<template>
  <div class="outline">
    <h1 class="page-title">大纲视图</h1>

    <!-- Toolbar -->
    <div class="toolbar">
      <n-button type="primary" @click="showCreateVolume = true">创建卷</n-button>
      <n-button @click="showCreateArc = true">创建节</n-button>
      <n-button @click="showCreateChapter = true">创建章节</n-button>
      <n-divider vertical />
      <n-button @click="handleBatchDownload">批量下载</n-button>
    </div>

    <!-- ═══ Book Section ═══ -->
    <div class="book-section">
      <div class="section-header">
        <h2 class="section-title">全书大纲</h2>
        <div class="section-header-actions">
          <n-button
            size="tiny"
            @click="showBookOutline = !showBookOutline"
          >{{ showBookOutline ? '收起' : '展开' }}</n-button>
          <n-button
            v-if="showBookOutline"
            size="tiny"
            :type="outlineMode.book === 'preview' ? 'primary' : 'default'"
            @click="toggleOutlineMode('book')"
          >{{ outlineMode.book === 'preview' ? '编辑' : '预览' }}</n-button>
          <n-button
            size="small"
            :loading="bookGenerating"
            @click="prepareGenerateBook"
          >生成全书大纲</n-button>
        </div>
      </div>
      <div v-if="showBookOutline && bookOutline" class="outline-text">
        <div v-if="outlineMode.book === 'preview'" class="markdown-preview" v-html="renderMarkdown(bookOutline)" />
        <n-input
          v-else
          v-model:value="bookOutline"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 12 }"
          placeholder="全书大纲内容..."
        />
        <div v-if="outlineMode.book === 'edit'" class="outline-actions">
          <n-button size="tiny" @click="handleSaveBookOutline">保存</n-button>
        </div>
      </div>
      <p v-if="!showBookOutline && bookOutline" class="outline-empty">全书大纲已生成（点击展开查看）</p>
      <p v-if="!bookOutline" class="outline-empty">尚未生成全书大纲</p>
    </div>

    <!-- Volume list -->
    <div v-if="store.volumes.length" class="volume-list">
      <div
        v-for="vol in store.volumes"
        :key="vol.id"
        class="volume-section"
      >
        <!-- Volume header -->
        <div class="volume-header">
          <h2 class="volume-title">
            <span class="volume-title-text">{{ vol.title }}</span>
          </h2>
          <div class="volume-meta">
            <span class="chapter-count">{{ chaptersByVolume(vol.id).length }} 章</span>
            <n-button size="tiny" @click="showVolumeOutline[vol.id] = !showVolumeOutline[vol.id]">
              {{ showVolumeOutline[vol.id] ? '收起' : '卷纲' }}
            </n-button>
            <n-button size="tiny" :loading="volGenerating[vol.id]" @click="prepareGenerateVolume(vol)">
              生成卷纲
            </n-button>
            <n-popconfirm @positive-click="handleDeleteVolume(vol.id)">
              <template #trigger>
                <n-button size="tiny" text class="delete-btn" @click.stop>删除卷</n-button>
              </template>
              确定删除此卷及其下所有章节？
            </n-popconfirm>
          </div>
        </div>

        <p v-if="vol.description" class="volume-desc">{{ vol.description }}</p>

        <!-- Volume outline fold panel -->
        <div v-if="showVolumeOutline[vol.id]" class="outline-text">
          <div class="outline-toolbar">
            <n-button
              size="tiny"
              :type="outlineMode[`vol_${vol.id}`] === 'preview' ? 'primary' : 'default'"
              @click="toggleOutlineMode(`vol_${vol.id}`)"
            >{{ outlineMode[`vol_${vol.id}`] === 'preview' ? '编辑' : '预览' }}</n-button>
          </div>
          <div v-if="outlineMode[`vol_${vol.id}`] === 'preview'" class="markdown-preview" v-html="renderMarkdown(volOutlines[vol.id])" />
          <n-input
            v-else
            v-model:value="volOutlines[vol.id]"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 8 }"
            placeholder="卷纲内容..."
          />
          <div v-if="outlineMode[`vol_${vol.id}`] === 'edit'" class="outline-actions">
            <n-button size="tiny" @click="handleSaveVolumeOutline(vol)">保存</n-button>
          </div>
        </div>

        <!-- Arc sections -->
        <div v-if="arcsByVolume(vol.id).length" class="arc-list">
          <div
            v-for="arc in arcsByVolume(vol.id)"
            :key="arc.id"
            class="arc-section"
          >
            <div class="arc-header">
              <span class="arc-title">{{ arc.title }}</span>
              <div class="arc-meta">
                <span class="chapter-count">{{ chaptersByArc(arc.id).length }} 章</span>
                <n-button size="tiny" @click="showArcOutline[arc.id] = !showArcOutline[arc.id]">
                  {{ showArcOutline[arc.id] ? '收起' : '节纲' }}
                </n-button>
                <n-button size="tiny" :loading="arcGenerating[arc.id]" @click="prepareGenerateArc(arc)">
                  生成节纲
                </n-button>
                <n-popconfirm @positive-click="handleDeleteArc(arc.id)">
                  <template #trigger>
                    <n-button size="tiny" text class="delete-btn" @click.stop>删除</n-button>
                  </template>
                  确定删除此节？
                </n-popconfirm>
              </div>
            </div>
            <p v-if="arc.description" class="arc-desc">{{ arc.description }}</p>

            <!-- Arc outline fold panel -->
            <div v-if="showArcOutline[arc.id]" class="outline-text">
              <div class="outline-toolbar">
                <n-button
                  size="tiny"
                  :type="outlineMode[`arc_${arc.id}`] === 'preview' ? 'primary' : 'default'"
                  @click="toggleOutlineMode(`arc_${arc.id}`)"
                >{{ outlineMode[`arc_${arc.id}`] === 'preview' ? '编辑' : '预览' }}</n-button>
              </div>
              <div v-if="outlineMode[`arc_${arc.id}`] === 'preview'" class="markdown-preview" v-html="renderMarkdown(arcOutlines[arc.id])" />
              <n-input
                v-else
                v-model:value="arcOutlines[arc.id]"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 6 }"
                placeholder="节纲内容..."
              />
              <div v-if="outlineMode[`arc_${arc.id}`] === 'edit'" class="outline-actions">
                <n-button size="tiny" @click="handleSaveArcOutline(arc)">保存</n-button>
              </div>
            </div>

            <!-- Chapter cards -->
            <div v-if="chaptersByArc(arc.id).length" class="chapter-list">
              <div
                v-for="ch in chaptersByArc(arc.id)"
                :key="ch.id"
                class="chapter-card"
                :class="[`status-${ch.status}`]"
                @click="$router.push(`/editor/${ch.id}`)"
              >
                <div class="chapter-body">
                  <h3 class="chapter-title">{{ ch.title }}</h3>
                  <p v-if="ch.summary || ch.ai_summary" class="chapter-summary">
                    {{ ch.ai_summary || ch.summary }}
                  </p>
                  <div v-if="ch.ai_summary" class="chapter-footer">
                    <n-tag size="small" type="info">AI 摘要</n-tag>
                  </div>
                  <div class="chapter-footer">
                    <n-tag size="small" :type="statusType(ch.status)">
                      {{ statusLabel(ch.status) }}
                    </n-tag>
                    <span class="word-count">{{ ch.word_count }} 字</span>
                  </div>
                </div>
                <div class="chapter-actions" @click.stop>
                  <n-button size="tiny" @click="handleGenerateChapter(ch)">生成</n-button>
                  <n-button size="tiny" @click="handleRegenerateSummary(ch)">重写摘要</n-button>
                  <n-button size="tiny" @click="handleDownloadChapter(ch)">下载</n-button>
                  <n-popconfirm @positive-click="handleDeleteChapter(ch.id, ch.volume_id)">
                    <template #trigger>
                      <n-button size="tiny" text class="delete-btn">删除</n-button>
                    </template>
                    确定删除此章节？
                  </n-popconfirm>
                </div>
              </div>
            </div>
            <div v-else class="empty-chapters">
              <n-empty description="该节下暂无章节" size="small" />
            </div>
          </div>
        </div>

        <!-- Unassigned chapters -->
        <div v-if="unassignedChapters(vol.id).length" class="unassigned-section">
          <div class="unassigned-header">未归属章节</div>
          <div class="chapter-list">
            <div
              v-for="ch in unassignedChapters(vol.id)"
              :key="ch.id"
              class="chapter-card"
              :class="[`status-${ch.status}`]"
              @click="$router.push(`/editor/${ch.id}`)"
            >
              <div class="chapter-body">
                <h3 class="chapter-title">{{ ch.title }}</h3>
                <p v-if="ch.summary" class="chapter-summary">{{ ch.summary }}</p>
                <div class="chapter-footer">
                  <n-tag size="small" :type="statusType(ch.status)">
                    {{ statusLabel(ch.status) }}
                  </n-tag>
                  <span class="word-count">{{ ch.word_count }} 字</span>
                </div>
              </div>
              <div class="chapter-actions" @click.stop>
                <n-button size="tiny" @click="handleGenerateChapter(ch)">生成</n-button>
                <n-button size="tiny" @click="handleDownloadChapter(ch)">下载</n-button>
                <n-popconfirm @positive-click="handleDeleteChapter(ch.id, ch.volume_id)">
                  <template #trigger>
                    <n-button size="tiny" text class="delete-btn">删除</n-button>
                  </template>
                  确定删除此章节？
                </n-popconfirm>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="empty-volume">
      <n-empty description="暂无卷，请先创建" />
    </div>

    <!-- Create Volume Modal -->
    <n-modal v-model:show="showCreateVolume" title="创建卷" preset="card" style="width: 480px">
      <n-form>
        <n-form-item label="卷标题">
          <n-input v-model:value="newVolume.title" placeholder="如：第一卷" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="newVolume.description" type="textarea" rows="3" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button type="primary" @click="handleCreateVolume">创建</n-button>
      </template>
    </n-modal>

    <!-- Create Arc Modal -->
    <n-modal v-model:show="showCreateArc" title="创建节" preset="card" style="width: 520px">
      <n-form>
        <n-form-item label="所属卷">
          <n-select
            v-model:value="newArc.volume_id"
            :options="volumeOptions"
            placeholder="选择卷"
          />
        </n-form-item>
        <n-form-item label="节标题">
          <n-input v-model:value="newArc.title" placeholder="如：第一章 开端" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="newArc.description" type="textarea" rows="3" placeholder="本节描述" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button type="primary" @click="handleCreateArc">创建</n-button>
      </template>
    </n-modal>

    <!-- Create Chapter Modal -->
    <n-modal v-model:show="showCreateChapter" title="创建章节" preset="card" style="width: 520px">
      <n-form>
        <n-form-item label="所属卷">
          <n-select
            v-model:value="newChapter.volume_id"
            :options="volumeOptions"
            placeholder="选择卷"
            @update:value="onVolumeChange"
          />
        </n-form-item>
        <n-form-item label="所属节">
          <n-select
            v-model:value="newChapter.arc_id"
            :options="arcOptionsForCreate"
            placeholder="选择节（可选）"
            clearable
          />
        </n-form-item>
        <n-form-item label="章节标题">
          <n-input v-model:value="newChapter.title" placeholder="如：第一章 开端" />
        </n-form-item>
        <n-form-item label="摘要">
          <n-input v-model:value="newChapter.summary" type="textarea" rows="3" placeholder="本章摘要" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button type="primary" @click="handleCreateChapter">创建</n-button>
      </template>
    </n-modal>

    <!-- ═══ SSE Generation Output Modal ═══ -->
    <n-modal v-model:show="showGenOutput" :mask-closable="false" style="width: 720px">
      <n-card :title="genTitle" style="max-height: 80vh; overflow-y: auto">
        <!-- User prompt input (shown when idle) -->
        <div v-if="genPhase === 'idle'" class="gen-prompt-section">
          <n-input
            v-model:value="userPrompt"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            placeholder="补充提示词（可选）：输入您对本次大纲生成的特定要求..."
          />
        </div>

        <!-- Generation output (shown when generating or done) -->
        <div v-if="genPhase !== 'idle'" class="gen-output">
          <p v-if="genModel" class="gen-meta">模型: {{ genModel }} | 预估: {{ genTokens }} tokens</p>

          <!-- During generation: raw streaming text -->
          <div v-if="genPhase === 'generating'" class="gen-text">{{ genOutput }}</div>

          <!-- After done: rendered markdown preview -->
          <div v-else class="gen-preview" v-html="renderMarkdown(genOutput)" />

          <n-spin v-if="genRunning" size="small" />
        </div>

        <template #action>
          <n-space justify="end">
            <template v-if="genPhase === 'idle'">
              <n-button @click="showGenOutput = false">取消</n-button>
              <n-button type="primary" @click="startGen">开始生成</n-button>
            </template>
            <template v-else-if="genPhase === 'generating'">
              <n-button @click="genAbort?.abort()">取消</n-button>
            </template>
            <template v-else>
              <n-button type="primary" @click="showGenOutput = false">关闭</n-button>
            </template>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { marked } from 'marked'
import { useChaptersStore } from '../stores/chapters.js'
import { useSettingsStore } from '../stores/settings.js'
import {
  createVolume, createChapter, deleteChapter, deleteVolume,
  downloadChapter, downloadAllChapters,
  createArc, deleteArc, updateArc,
  updateVolume,
} from '../api/chapters.js'
import {
  generateArcOutline, generateVolumeOutline, generateBookOutline,
  regenerateSummary,
} from '../api/generate.js'

const router = useRouter()
const message = useMessage()
const store = useChaptersStore()
const settingsStore = useSettingsStore()

const showCreateVolume = ref(false)
const showCreateChapter = ref(false)
const showCreateArc = ref(false)

const newVolume = ref({ title: '', description: '' })
const newChapter = ref({ volume_id: null, arc_id: null, title: '', summary: '' })
const newArc = ref({ volume_id: null, title: '', description: '' })

// Volume/Arc outline display state
const showVolumeOutline = reactive({})
const showArcOutline = reactive({})
const volOutlines = reactive({})
const arcOutlines = reactive({})

// Outline edit/preview mode
const outlineMode = reactive({ book: 'preview' })

function toggleOutlineMode(key) {
  outlineMode[key] = outlineMode[key] === 'preview' ? 'edit' : 'preview'
}

// Book outline
const bookOutline = ref('')
const showBookOutline = ref(false)

// ── Generation modal state ────────────────────────────────
const showGenOutput = ref(false)
const genTitle = ref('')
const genOutput = ref('')
const genModel = ref('')
const genTokens = ref(0)
const genRunning = ref(false)
const genAbort = ref(null)
const genPhase = ref('idle') // 'idle' | 'generating' | 'done'
const userPrompt = ref('')

// Store the generation function to call when user clicks "开始生成"
let pendingGenStart = null

const bookGenerating = ref(false)
const volGenerating = reactive({})
const arcGenerating = reactive({})

const volumeOptions = computed(() =>
  store.volumes.map(v => ({ label: v.title, value: v.id }))
)

const arcOptionsForCreate = computed(() => {
  if (!newChapter.value.volume_id) return []
  return store.arcs
    .filter(a => a.volume_id === newChapter.value.volume_id)
    .map(a => ({ label: a.title, value: a.id }))
})

const chaptersByVolume = (volId) =>
  store.chapters.filter(c => c.volume_id === volId)

const arcsByVolume = (volId) =>
  store.arcs.filter(a => a.volume_id === volId)

const chaptersByArc = (arcId) =>
  store.chapters.filter(c => c.arc_id === arcId)

const unassignedChapters = (volId) =>
  store.chapters.filter(c => c.volume_id === volId && !c.arc_id)

const statusType = (s) =>
  ({ pending: 'default', generating: 'warning', completed: 'success' }[s] || 'default')

const statusLabel = (s) =>
  ({ pending: '待生成', generating: '生成中', completed: '已完成' }[s] || s)

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch {
    return text
  }
}

function onVolumeChange(volId) {
  newChapter.value.arc_id = null
}

function openGenModal(title) {
  genTitle.value = title
  genOutput.value = ''
  genModel.value = ''
  genTokens.value = 0
  genRunning.value = false
  genPhase.value = 'idle'
  userPrompt.value = ''
  showGenOutput.value = true
}

function startGen() {
  if (!pendingGenStart) return
  genPhase.value = 'generating'
  genRunning.value = true
  pendingGenStart(userPrompt.value)
}

async function runOutlineSSE(label, urlFn, onContentDone) {
  openGenModal(label)
  pendingGenStart = (prompt) => {
    genAbort.value = urlFn({
      onStart: (evt) => {
        genModel.value = evt.model || ''
        genTokens.value = evt.token_estimate || 0
      },
      onToken: (token) => {
        genOutput.value += token
      },
      onDone: (evt) => {
        genRunning.value = false
        genPhase.value = 'done'
        const content = evt?.content || genOutput.value
        if (onContentDone && content) {
          onContentDone(content)
        }
        message.success(`${label} 生成完成`)
      },
      onError: (err) => {
        genRunning.value = false
        genPhase.value = 'done'
        message.error(err)
      },
    }, { user_prompt: prompt })
  }
}

// ── Handlers ──────────────────────────────────────────────

async function handleCreateVolume() {
  await createVolume(newVolume.value)
  newVolume.value = { title: '', description: '' }
  showCreateVolume.value = false
  await store.fetchVolumes()
  message.success('卷已创建')
}

async function handleCreateArc() {
  if (!newArc.value.volume_id) {
    message.warning('请选择所属卷')
    return
  }
  await createArc(newArc.value)
  newArc.value = { volume_id: null, title: '', description: '' }
  showCreateArc.value = false
  await store.fetchArcs()
  message.success('节已创建')
}

async function handleCreateChapter() {
  await createChapter(newChapter.value)
  newChapter.value = { volume_id: null, arc_id: null, title: '', summary: '' }
  showCreateChapter.value = false
  await store.fetchChapters()
  message.success('章节已创建')
}

async function handleDeleteVolume(id) {
  await deleteVolume(id)
  await store.fetchVolumes()
  await store.fetchChapters()
  await store.fetchArcs()
  message.success('卷已删除')
}

async function handleDeleteChapter(id, volumeId) {
  await deleteChapter(id)
  await store.fetchChapters(volumeId)
  message.success('章节已删除')
}

async function handleDeleteArc(id) {
  await deleteArc(id)
  await store.fetchArcs()
  await store.fetchChapters()
  message.success('节已删除')
}

function handleGenerateChapter(ch) {
  router.push(`/editor/${ch.id}?generate=1`)
}

async function handleRegenerateSummary(ch) {
  try {
    const res = await regenerateSummary(ch.id)
    ch.ai_summary = res.summary
    message.success('摘要已重写')
  } catch (e) {
    message.error(e.message || '重写摘要失败')
  }
}

async function handleDownloadChapter(ch) {
  const res = await downloadChapter(ch.id)
  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = `${ch.title || 'chapter'}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

async function handleBatchDownload() {
  const res = await downloadAllChapters()
  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = 'chapters.zip'
  a.click()
  URL.revokeObjectURL(url)
}

// ── Outline generation ────────────────────────────────────

function prepareGenerateBook() {
  bookGenerating.value = true
  runOutlineSSE('全书大纲', (handlers) => generateBookOutline(handlers), (content) => {
    bookOutline.value = content
  })
}

function prepareGenerateVolume(vol) {
  volGenerating[vol.id] = true
  runOutlineSSE(`卷纲: ${vol.title}`, (handlers) => generateVolumeOutline(vol.id, handlers), (content) => {
    volOutlines[vol.id] = content
  })
}

function prepareGenerateArc(arc) {
  arcGenerating[arc.id] = true
  runOutlineSSE(`节纲: ${arc.title}`, (handlers) => generateArcOutline(arc.id, handlers), (content) => {
    arcOutlines[arc.id] = content
  })
}

// Reset loading states when modal closes
watch(showGenOutput, (val) => {
  if (!val) {
    bookGenerating.value = false
    // clear all vol/arc generating states
    for (const k of Object.keys(volGenerating)) volGenerating[k] = false
    for (const k of Object.keys(arcGenerating)) arcGenerating[k] = false
  }
})

// ── Save outlines ─────────────────────────────────────────

async function handleSaveBookOutline() {
  settingsStore.bookOutline = bookOutline.value
  await settingsStore.saveBookOutline()
  message.success('全书大纲已保存')
}

async function handleSaveVolumeOutline(vol) {
  await updateVolume(vol.id, { outline: volOutlines[vol.id] })
  message.success('卷纲已保存')
}

async function handleSaveArcOutline(arc) {
  if (arcOutlines[arc.id] !== undefined) {
    await updateArc(arc.id, { outline: arcOutlines[arc.id] })
  }
  message.success('节纲已保存')
}

onMounted(async () => {
  await Promise.all([
    store.fetchVolumes(),
    store.fetchChapters(),
    store.fetchArcs(),
    settingsStore.fetchBookOutline(),
  ])
  bookOutline.value = settingsStore.bookOutline

  // Initialize outline displays (collapsed by default) and store values
  for (const vol of store.volumes) {
    showVolumeOutline[vol.id] = false
    volOutlines[vol.id] = vol.outline || ''
    outlineMode[`vol_${vol.id}`] = 'preview'
  }
  for (const arc of store.arcs) {
    showArcOutline[arc.id] = false
    arcOutlines[arc.id] = arc.outline || ''
    outlineMode[`arc_${arc.id}`] = 'preview'
  }
})
</script>

<style scoped>
.outline {
  max-width: 960px;
  margin: 0 auto;
}

.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 20px;
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

/* Book section */
.book-section {
  margin-bottom: 28px;
  padding: 16px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-accent);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-accent-dark);
  margin: 0;
}

/* Volume */
.volume-section {
  margin-bottom: 28px;
  animation: fade-in-up 0.4s ease both;
}

.volume-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0 6px;
}

.volume-title {
  margin: 0;
}

.volume-title-text {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-accent-dark);
  letter-spacing: 1px;
}

.volume-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.chapter-count {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.volume-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
  line-height: 1.5;
}

/* Outline text */
.outline-text {
  margin: 8px 0 12px;
}

.outline-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 6px;
}

.outline-actions {
  margin-top: 6px;
}

.outline-empty {
  font-size: 13px;
  color: var(--color-text-muted);
  margin: 0;
}

/* Markdown preview */
.markdown-preview {
  padding: 12px 16px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-primary);
  overflow-x: auto;
}

.markdown-preview :deep(h1),
.markdown-preview :deep(h2),
.markdown-preview :deep(h3),
.markdown-preview :deep(h4) {
  font-family: var(--font-display);
  font-weight: 600;
  margin: 1em 0 0.5em;
  color: var(--color-accent-dark);
}

.markdown-preview :deep(h1) { font-size: 1.4em; }
.markdown-preview :deep(h2) { font-size: 1.2em; }
.markdown-preview :deep(h3) { font-size: 1.1em; }

.markdown-preview :deep(p) {
  margin: 0 0 0.6em;
}

.markdown-preview :deep(ul),
.markdown-preview :deep(ol) {
  padding-left: 1.5em;
  margin: 0.4em 0;
}

.markdown-preview :deep(li) {
  margin: 0.2em 0;
}

.markdown-preview :deep(strong) {
  font-weight: 600;
}

.markdown-preview :deep(code) {
  background: rgba(201, 169, 78, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
}

.markdown-preview :deep(pre) {
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  padding: 12px;
  overflow-x: auto;
}

.markdown-preview :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-preview :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 1em 0;
}

.markdown-preview :deep(blockquote) {
  border-left: 3px solid var(--color-accent);
  margin: 0.5em 0;
  padding: 4px 12px;
  color: var(--color-text-secondary);
  background: rgba(201, 169, 78, 0.04);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.markdown-preview :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
}

.markdown-preview :deep(th),
.markdown-preview :deep(td) {
  border: 1px solid var(--color-border);
  padding: 6px 10px;
  text-align: left;
}

.markdown-preview :deep(th) {
  background: var(--color-bg-page);
  font-weight: 600;
}

/* Arc */
.arc-list {
  margin: 12px 0 0 16px;
  border-left: 2px solid var(--color-border-light);
  padding-left: 16px;
}

.arc-section {
  margin-bottom: 16px;
  animation: fade-in-up 0.35s ease both;
}

.arc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.arc-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.arc-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.arc-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 8px;
  line-height: 1.5;
}

/* Unassigned */
.unassigned-section {
  margin: 12px 0 0 16px;
  padding-left: 16px;
}

.unassigned-header {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-bottom: 8px;
  padding: 4px 8px;
  background: var(--color-bg-page);
  border-radius: var(--radius-sm);
  display: inline-block;
}

/* Chapter list */
.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chapter-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  cursor: pointer;
  border-left: 3px solid var(--color-border);
  transition: background var(--transition-fast), box-shadow var(--transition-fast);
  animation: fade-in-up 0.35s ease both;
}

.chapter-card:hover {
  background: rgba(201, 169, 78, 0.04);
  box-shadow: var(--shadow-sm);
}

.chapter-card.status-pending {
  border-left-color: var(--color-accent);
}

.chapter-card.status-generating {
  border-left-color: var(--color-warning);
}

.chapter-card.status-completed {
  border-left-color: var(--color-success);
}

.chapter-body {
  flex: 1;
  min-width: 0;
}

.chapter-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px;
}

.chapter-summary {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 8px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.chapter-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.word-count {
  font-size: 12px;
  color: var(--color-text-muted);
}

.chapter-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.delete-btn {
  color: var(--color-text-muted) !important;
  font-size: 12px;
}

.delete-btn:hover {
  color: var(--color-error) !important;
}

.empty-chapters {
  padding: 12px 0;
}

.empty-volume {
  margin-top: 60px;
}

/* Generation modal */
.gen-prompt-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.gen-output {
  min-height: 150px;
}

.gen-meta {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
}

.gen-text {
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.gen-preview {
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-primary);
}

.gen-preview :deep(h1),
.gen-preview :deep(h2),
.gen-preview :deep(h3),
.gen-preview :deep(h4) {
  font-family: var(--font-display);
  font-weight: 600;
  margin: 1em 0 0.5em;
  color: var(--color-accent-dark);
}

.gen-preview :deep(h1) { font-size: 1.4em; }
.gen-preview :deep(h2) { font-size: 1.2em; }
.gen-preview :deep(h3) { font-size: 1.1em; }

.gen-preview :deep(p) {
  margin: 0 0 0.6em;
}

.gen-preview :deep(ul),
.gen-preview :deep(ol) {
  padding-left: 1.5em;
  margin: 0.4em 0;
}

.gen-preview :deep(li) {
  margin: 0.2em 0;
}

.gen-preview :deep(strong) {
  font-weight: 600;
}

.gen-preview :deep(code) {
  background: rgba(201, 169, 78, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
}

.gen-preview :deep(pre) {
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  padding: 12px;
  overflow-x: auto;
}

.gen-preview :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 1em 0;
}
</style>
