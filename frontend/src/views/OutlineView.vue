<template>
  <div class="outline-container">
    <!-- ═══ Glassmorphism Floating Toolbar ═══ -->
    <div class="toolbar-wrapper">
      <div class="toolbar">
        <div class="toolbar-left">
          <h1 class="page-title">大纲</h1>
          <span class="page-subtitle">全书结构总览</span>
        </div>
        <div class="toolbar-right">
          <button class="tb-btn tb-btn-primary" @click="showCreateVolume = true">
            <span class="tb-icon">＋</span>
            <span>新建卷</span>
          </button>
          <button class="tb-btn" @click="showCreateArc = true">
            <span class="tb-icon">⊕</span>
            <span>新建节</span>
          </button>
          <button class="tb-btn" @click="showCreateChapter = true">
            <span class="tb-icon">📄</span>
            <span>新建章节</span>
          </button>
          <div class="tb-divider" />
          <button class="tb-btn tb-btn-ghost" @click="handleBatchDownload">
            <span class="tb-icon">↓</span>
            <span>批量下载</span>
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ Book Outline — Preface Card ═══ -->
    <div class="preface-card">
      <div class="preface-header" @click="showBookOutline = !showBookOutline">
        <div class="preface-title-group">
          <div class="preface-icon">📖</div>
          <div>
            <h2 class="preface-title">全书大纲</h2>
            <span class="preface-meta">总体规划 · 故事蓝图</span>
          </div>
        </div>
        <div class="preface-actions">
          <span class="preface-badge" :class="{ active: showBookOutline }">
            {{ showBookOutline ? '展开中' : '已收起' }}
          </span>
          <button
            v-if="showBookOutline && bookOutline"
            class="preface-toggle"
            :class="{ active: outlineMode.book === 'preview' }"
            @click.stop="toggleOutlineMode('book')"
          >
            {{ outlineMode.book === 'preview' ? '预览' : '编辑' }}
          </button>
          <button
            class="preface-gen-btn"
            :class="{ loading: bookGenerating }"
            :disabled="bookGenerating"
            @click.stop="prepareGenerateBook"
          >
            <span v-if="bookGenerating" class="spin" />
            <span v-else>✦</span>
            <span>生成</span>
          </button>
          <button class="preface-chevron" :class="{ open: showBookOutline }">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
      <transition name="outline-slide">
        <div v-if="showBookOutline" class="preface-body">
          <div v-if="bookOutline" class="outline-editor">
            <div v-if="outlineMode.book === 'preview'" class="markdown-body" v-html="renderMarkdown(bookOutline)" />
            <textarea
              v-else
              v-model="bookOutline"
              class="outline-textarea"
              placeholder="输入全书大纲内容..."
              rows="4"
            />
            <div v-if="outlineMode.book === 'edit'" class="outline-save-row">
              <button class="save-btn" @click="handleSaveBookOutline">保存修改</button>
            </div>
          </div>
          <div v-else class="preface-empty">
            <p>尚未生成全书大纲</p>
            <p class="preface-empty-hint">点击上方「生成」按钮，AI 将为您构建完整的故事蓝图</p>
          </div>
        </div>
      </transition>
    </div>

    <!-- ═══ Volumes ═══ -->
    <div v-if="store.volumes.length" class="volumes-container">
      <div
        v-for="(vol, vIdx) in store.volumes"
        :key="vol.id"
        class="volume-card"
        :style="{ '--v-delay': `${vIdx * 0.08}s` }"
      >
        <!-- Volume Header -->
        <div class="volume-header">
          <div class="volume-header-top">
            <div class="volume-title-group" @click="showVolumeOutline[vol.id] = !showVolumeOutline[vol.id]">
              <div class="volume-number">{{ formatVolumeNum(vIdx) }}</div>
              <h2 class="volume-title">{{ vol.title }}</h2>
            </div>
            <div class="volume-header-actions">
              <div class="volume-stat">
                <span class="stat-num">{{ chaptersByVolume(vol.id).length }}</span>
                <span class="stat-label">章</span>
              </div>
              <div class="volume-progress">
                <div class="progress-track">
                  <div
                    class="progress-fill"
                    :style="{ width: volumeProgress(vol.id) + '%' }"
                  />
                </div>
              </div>
              <button
                class="vol-btn"
                @click="showVolumeOutline[vol.id] = !showVolumeOutline[vol.id]"
                :class="{ active: showVolumeOutline[vol.id] }"
              >
                卷纲
              </button>
              <button
                class="vol-btn vol-gen-btn"
                :class="{ loading: volGenerating[vol.id] }"
                :disabled="volGenerating[vol.id]"
                @click="prepareGenerateVolume(vol)"
              >
                <span v-if="volGenerating[vol.id]" class="spin" />
                <span>生成卷纲</span>
              </button>
              <button class="vol-btn vol-del-btn" @click="confirmDeleteVolume(vol)">删除</button>
            </div>
          </div>
          <p v-if="vol.description" class="volume-desc">{{ vol.description }}</p>

          <!-- Decorative divider -->
          <div class="vol-divider">
            <span class="vol-divider-ornament">◈</span>
          </div>
        </div>

        <!-- Volume Outline -->
        <transition name="outline-slide">
          <div v-if="showVolumeOutline[vol.id]" class="volume-outline">
            <div v-if="volOutlines[vol.id]" class="outline-editor">
              <div v-if="outlineMode[`vol_${vol.id}`] === 'preview'" class="markdown-body" v-html="renderMarkdown(volOutlines[vol.id])" />
              <textarea
                v-else
                v-model="volOutlines[vol.id]"
                class="outline-textarea"
                placeholder="卷纲内容..."
                rows="3"
              />
              <div v-if="outlineMode[`vol_${vol.id}`] === 'edit'" class="outline-save-row">
                <button class="save-btn" @click="handleSaveVolumeOutline(vol)">保存修改</button>
              </div>
            </div>
            <div v-else class="volume-outline-empty">
              <span>尚未生成卷纲</span>
            </div>
            <div class="outline-mode-toggle">
              <button
                class="mode-btn"
                :class="{ active: outlineMode[`vol_${vol.id}`] === 'preview' }"
                @click="outlineMode[`vol_${vol.id}`] = 'preview'"
              >预览</button>
              <button
                class="mode-btn"
                :class="{ active: outlineMode[`vol_${vol.id}`] === 'edit' }"
                @click="outlineMode[`vol_${vol.id}`] = 'edit'"
              >编辑</button>
            </div>
          </div>
        </transition>

        <!-- Arcs + Chapters Tree -->
        <div class="arcs-tree">
          <!-- Arcs -->
          <div
            v-for="(arc, aIdx) in arcsByVolume(vol.id)"
            :key="arc.id"
            class="arc-node"
            :style="{ '--a-delay': `${aIdx * 0.06}s` }"
          >
            <div class="arc-connector">
              <div class="arc-line" />
              <div class="arc-dot" />
            </div>
            <div class="arc-content">
              <!-- Arc Header -->
              <div class="arc-header" @click="showArcOutline[arc.id] = !showArcOutline[arc.id]">
                <div class="arc-title-group">
                  <span class="arc-num">{{ formatArcNum(aIdx) }}</span>
                  <span class="arc-title">{{ arc.title }}</span>
                  <span class="arc-chapter-count">{{ chaptersByArc(arc.id).length }}章</span>
                </div>
                <div class="arc-actions">
                  <button
                    class="arc-btn"
                    :class="{ active: showArcOutline[arc.id] }"
                    @click.stop="showArcOutline[arc.id] = !showArcOutline[arc.id]"
                  >
                    节纲
                  </button>
                  <button
                    class="arc-btn arc-gen-btn"
                    :class="{ loading: arcGenerating[arc.id] }"
                    :disabled="arcGenerating[arc.id]"
                    @click.stop="prepareGenerateArc(arc)"
                  >
                    <span v-if="arcGenerating[arc.id]" class="spin" />
                    <span>生成</span>
                  </button>
                  <button
                    class="arc-btn arc-del-btn"
                    @click.stop="confirmDeleteArc(arc)"
                  >删除</button>
                </div>
              </div>

              <p v-if="arc.description" class="arc-desc">{{ arc.description }}</p>

              <!-- Arc Outline -->
              <transition name="outline-slide">
                <div v-if="showArcOutline[arc.id]" class="arc-outline-section">
                  <div v-if="arcOutlines[arc.id]" class="outline-editor">
                    <div v-if="outlineMode[`arc_${arc.id}`] === 'preview'" class="markdown-body" v-html="renderMarkdown(arcOutlines[arc.id])" />
                    <textarea
                      v-else
                      v-model="arcOutlines[arc.id]"
                      class="outline-textarea"
                      placeholder="节纲内容..."
                      rows="3"
                    />
                    <div v-if="outlineMode[`arc_${arc.id}`] === 'edit'" class="outline-save-row">
                      <button class="save-btn" @click="handleSaveArcOutline(arc)">保存修改</button>
                    </div>
                  </div>
                  <div v-else class="arc-outline-empty">
                    <span>尚未生成节纲</span>
                  </div>
                  <div class="outline-mode-toggle">
                    <button
                      class="mode-btn"
                      :class="{ active: outlineMode[`arc_${arc.id}`] === 'preview' }"
                      @click="outlineMode[`arc_${arc.id}`] = 'preview'"
                    >预览</button>
                    <button
                      class="mode-btn"
                      :class="{ active: outlineMode[`arc_${arc.id}`] === 'edit' }"
                      @click="outlineMode[`arc_${arc.id}`] = 'edit'"
                    >编辑</button>
                  </div>
                </div>
              </transition>

              <!-- Chapter Cards -->
              <div v-if="chaptersByArc(arc.id).length" class="chapter-list">
                <div
                  v-for="(ch, cIdx) in chaptersByArc(arc.id)"
                  :key="ch.id"
                  class="chapter-card"
                  :class="`status-${ch.status}`"
                  :style="{ '--c-delay': `${cIdx * 0.04}s` }"
                  @click="$router.push(`/editor/${ch.id}`)"
                >
                  <div class="chapter-strip" />
                  <div class="chapter-inner">
                    <div class="chapter-main">
                      <h3 class="chapter-title">{{ ch.title }}</h3>
                      <p v-if="ch.ai_summary || ch.summary" class="chapter-summary">
                        {{ ch.ai_summary || ch.summary }}
                      </p>
                    </div>
                    <div class="chapter-side">
                      <span class="chapter-status-tag" :class="`tag-${ch.status}`">
                        {{ statusLabel(ch.status) }}
                      </span>
                      <span class="chapter-wordcount">{{ ch.word_count }} 字</span>
                    </div>
                    <div class="chapter-actions" @click.stop>
                      <button class="ch-action-btn" @click="handleGenerateChapter(ch)">
                        <span class="ch-action-icon">▶</span>生成
                      </button>
                      <button class="ch-action-btn" @click="handleRegenerateSummary(ch)">
                        <span class="ch-action-icon">↻</span>摘要
                      </button>
                      <button class="ch-action-btn" @click="handleDownloadChapter(ch)">
                        <span class="ch-action-icon">↓</span>下载
                      </button>
                      <button class="ch-action-btn ch-action-danger" @click="confirmDeleteChapter(ch)">
                        <span class="ch-action-icon">✕</span>删除
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="chapter-empty">
                <span>该节下暂无章节</span>
              </div>
            </div>
          </div>

          <!-- Unassigned Chapters -->
          <div
            v-if="unassignedChapters(vol.id).length"
            class="arc-node"
          >
            <div class="arc-connector">
              <div class="arc-line" />
              <div class="arc-dot arc-dot-muted" />
            </div>
            <div class="arc-content">
              <div class="arc-header">
                <div class="arc-title-group">
                  <span class="arc-num">—</span>
                  <span class="arc-title arc-title-muted">未归属章节</span>
                </div>
              </div>
              <div class="chapter-list">
                <div
                  v-for="(ch, cIdx) in unassignedChapters(vol.id)"
                  :key="ch.id"
                  class="chapter-card"
                  :class="`status-${ch.status}`"
                  :style="{ '--c-delay': `${cIdx * 0.04}s` }"
                  @click="$router.push(`/editor/${ch.id}`)"
                >
                  <div class="chapter-strip" />
                  <div class="chapter-inner">
                    <div class="chapter-main">
                      <h3 class="chapter-title">{{ ch.title }}</h3>
                      <p v-if="ch.summary" class="chapter-summary">{{ ch.summary }}</p>
                    </div>
                    <div class="chapter-side">
                      <span class="chapter-status-tag" :class="`tag-${ch.status}`">
                        {{ statusLabel(ch.status) }}
                      </span>
                      <span class="chapter-wordcount">{{ ch.word_count }} 字</span>
                    </div>
                    <div class="chapter-actions" @click.stop>
                      <button class="ch-action-btn" @click="handleGenerateChapter(ch)">
                        <span class="ch-action-icon">▶</span>生成
                      </button>
                      <button class="ch-action-btn" @click="handleDownloadChapter(ch)">
                        <span class="ch-action-icon">↓</span>下载
                      </button>
                      <button class="ch-action-btn ch-action-danger" @click="confirmDeleteChapter(ch)">
                        <span class="ch-action-icon">✕</span>删除
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <div class="empty-icon">📝</div>
      <h3 class="empty-title">开始构建您的小说</h3>
      <p class="empty-desc">创建第一个卷，开启您的创作之旅</p>
      <button class="empty-cta" @click="showCreateVolume = true">
        <span>＋</span> 创建第一卷
      </button>
    </div>

    <!-- ═══ Create Volume Modal ═══ -->
    <n-modal v-model:show="showCreateVolume" title="新建卷" preset="card" style="width: 480px; border-radius: 12px">
      <n-form>
        <n-form-item label="卷标题">
          <n-input v-model:value="newVolume.title" placeholder="如：第一卷" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="newVolume.description" type="textarea" rows="3" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showCreateVolume = false">取消</n-button>
          <n-button type="primary" @click="handleCreateVolume">创建</n-button>
        </div>
      </template>
    </n-modal>

    <!-- Create Arc Modal -->
    <n-modal v-model:show="showCreateArc" title="新建节" preset="card" style="width: 520px">
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
        <div class="modal-footer">
          <n-button @click="showCreateArc = false">取消</n-button>
          <n-button type="primary" @click="handleCreateArc">创建</n-button>
        </div>
      </template>
    </n-modal>

    <!-- Create Chapter Modal -->
    <n-modal v-model:show="showCreateChapter" title="新建章节" preset="card" style="width: 520px">
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
        <div class="modal-footer">
          <n-button @click="showCreateChapter = false">取消</n-button>
          <n-button type="primary" @click="handleCreateChapter">创建</n-button>
        </div>
      </template>
    </n-modal>

    <!-- ═══ SSE Generation Output Modal ═══ -->
    <n-modal v-model:show="showGenOutput" :mask-closable="false" style="width: 720px">
      <n-card :title="genTitle" style="max-height: 80vh; overflow-y: auto; border-radius: 12px">
        <div v-if="genPhase === 'idle'" class="gen-prompt-section">
          <n-input
            v-model:value="userPrompt"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            placeholder="补充提示词（可选）：输入您对本次大纲生成的特定要求..."
          />
        </div>
        <div v-if="genPhase !== 'idle'" class="gen-output">
          <p v-if="genModel" class="gen-meta">模型: {{ genModel }} | 预估: {{ genTokens }} tokens</p>
          <div v-if="genPhase === 'generating'" class="gen-text">{{ genOutput }}</div>
          <div v-else class="markdown-body" v-html="renderMarkdown(genOutput)" />
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

    <!-- ═══ Confirm Delete Dialog ═══ -->
    <n-modal v-model:show="showDeleteConfirm" title="确认删除" preset="card" style="width: 400px">
      <p style="margin: 0; color: var(--color-text-secondary);">{{ deleteMessage }}</p>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showDeleteConfirm = false">取消</n-button>
          <n-button type="error" @click="executeDelete">删除</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { marked } from 'marked'
import { useChaptersStore } from '../stores/chapters.js'
import { useSettingsStore } from '../stores/settings.js'
import { useBooksStore } from '../stores/books.js'
import {
  createVolume, createChapter, deleteChapter, deleteVolume,
  downloadChapter, downloadAllChapters,
  createArc, deleteArc, updateArc,
  updateVolume,
} from '../api/chapters.js'
import {
  generateArcOutline, generateVolumeOutline, generateBookOutline,
  generateBookOutlineScoped,
  regenerateSummary,
} from '../api/generate.js'
import { getBookOutline, updateBookOutline } from '../api/books.js'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const store = useChaptersStore()
const settingsStore = useSettingsStore()
const booksStore = useBooksStore()

const bookId = computed(() => {
  return route.params.bookId ? Number(route.params.bookId) : booksStore.currentBookId
})

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
const bookOutlineCache = ref('')
const showBookOutline = ref(false)

async function loadBookOutline(bId) {
  try {
    const res = await getBookOutline(bId)
    bookOutlineCache.value = res.data?.outline || ''
    bookOutline.value = bookOutlineCache.value
  } catch {
    bookOutlineCache.value = ''
  }
}

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

// ── Delete confirm state ──
const showDeleteConfirm = ref(false)
const deleteMessage = ref('')
let pendingDelete = null

function confirmDeleteVolume(vol) {
  deleteMessage.value = `确定删除「${vol.title}」及其下所有章节？此操作不可撤销。`
  pendingDelete = async () => {
    await handleDeleteVolume(vol.id)
  }
  showDeleteConfirm.value = true
}

function confirmDeleteArc(arc) {
  deleteMessage.value = `确定删除节「${arc.title}」？其下的章节将变为未归属状态。`
  pendingDelete = async () => {
    await handleDeleteArc(arc.id)
  }
  showDeleteConfirm.value = true
}

function confirmDeleteChapter(ch) {
  deleteMessage.value = `确定删除章节「${ch.title}」？此操作不可撤销。`
  pendingDelete = async () => {
    await handleDeleteChapter(ch.id, ch.volume_id)
  }
  showDeleteConfirm.value = true
}

async function executeDelete() {
  if (pendingDelete) await pendingDelete()
  showDeleteConfirm.value = false
  pendingDelete = null
}

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

function formatVolumeNum(idx) {
  const nums = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
  return nums[idx] || `${idx + 1}`
}

function formatArcNum(idx) {
  const nums = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
  return `第${nums[idx] || idx + 1}节`
}

function volumeProgress(volId) {
  const chs = chaptersByVolume(volId)
  if (!chs.length) return 0
  const done = chs.filter(c => c.status === 'completed').length
  return Math.round((done / chs.length) * 100)
}

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
  const bId = bookId.value
  const genFn = bId
    ? (handlers) => generateBookOutlineScoped(bId, handlers)
    : (handlers) => generateBookOutline(handlers)
  runOutlineSSE('全书大纲', genFn, (content) => {
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
    for (const k of Object.keys(volGenerating)) volGenerating[k] = false
    for (const k of Object.keys(arcGenerating)) arcGenerating[k] = false
  }
})

// ── Save outlines ─────────────────────────────────────────

async function handleSaveBookOutline() {
  const bId = bookId.value
  if (bId) {
    await updateBookOutline(bId, bookOutline.value)
  } else {
    settingsStore.bookOutline = bookOutline.value
    await settingsStore.saveBookOutline()
  }
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
  const bId = bookId.value || undefined
  await Promise.all([
    store.fetchVolumes(bId),
    store.fetchChapters(undefined, bId),
    store.fetchArcs(undefined, bId),
    bId ? loadBookOutline(bId) : settingsStore.fetchBookOutline(),
  ])
  bookOutline.value = bId ? (bookOutlineCache || settingsStore.bookOutline) : settingsStore.bookOutline

  // Also ensure the books store loads the current book
  if (bId && !booksStore.currentBook) {
    booksStore.selectBook(bId).catch(() => {})
  }

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
/* ═══════════════════════════════════════════════
   OUTLINE VIEW — "Author's Archive"
   Editorial magazine aesthetic with literary warmth
   ═══════════════════════════════════════════════ */

.outline-container {
  max-width: 1000px;
  margin: 0 auto;
  padding-bottom: 80px;
}

/* ── Glassmorphism Toolbar ── */
.toolbar-wrapper {
  position: sticky;
  top: 0;
  z-index: 50;
  padding: 12px 0 20px;
  margin: -12px 0 0;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: rgba(250, 245, 237, 0.75);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  border: 1px solid rgba(232, 224, 213, 0.6);
  border-radius: 14px;
  box-shadow: 0 2px 12px rgba(26, 22, 20, 0.06);
}

.toolbar-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: 2px;
}

.page-subtitle {
  font-size: 13px;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tb-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: #fff;
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: var(--font-ui);
}

.tb-btn:hover {
  border-color: var(--color-accent);
  background: rgba(201, 169, 78, 0.06);
}

.tb-btn-primary {
  background: var(--color-accent);
  color: #fff;
  border-color: var(--color-accent);
}
.tb-btn-primary:hover {
  background: var(--color-accent-light);
  border-color: var(--color-accent-light);
}

.tb-btn-ghost {
  border-color: transparent;
  background: transparent;
  color: var(--color-text-secondary);
}
.tb-btn-ghost:hover {
  background: rgba(201, 169, 78, 0.08);
  color: var(--color-text-primary);
}

.tb-icon {
  font-size: 14px;
  line-height: 1;
}

.tb-divider {
  width: 1px;
  height: 22px;
  background: var(--color-border);
  margin: 0 6px;
}

/* ── Preface Card (全书大纲) ── */
.preface-card {
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  margin-bottom: 24px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-base);
}
.preface-card:hover {
  box-shadow: var(--shadow-md);
}

.preface-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  cursor: pointer;
  user-select: none;
}

.preface-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preface-icon {
  font-size: 22px;
  line-height: 1;
}

.preface-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: 1px;
}

.preface-meta {
  font-size: 12px;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
}

.preface-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preface-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--color-border-light);
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  transition: all var(--transition-fast);
}
.preface-badge.active {
  background: rgba(201, 169, 78, 0.12);
  color: var(--color-accent-dark);
}

.preface-toggle {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-family: var(--font-ui);
  transition: all var(--transition-fast);
}
.preface-toggle:hover,
.preface-toggle.active {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
}
.preface-toggle.active {
  background: rgba(201, 169, 78, 0.08);
}

.preface-gen-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 3px 12px;
  border-radius: 6px;
  border: 1px solid var(--color-accent);
  background: rgba(201, 169, 78, 0.08);
  color: var(--color-accent-dark);
  cursor: pointer;
  font-family: var(--font-ui);
  font-weight: 500;
  transition: all var(--transition-fast);
}
.preface-gen-btn:hover {
  background: var(--color-accent);
  color: #fff;
}
.preface-gen-btn.loading {
  opacity: 0.6;
  pointer-events: none;
}

.preface-chevron {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: transform var(--transition-base);
}
.preface-chevron.open {
  transform: rotate(180deg);
}

.preface-body {
  border-top: 1px solid var(--color-border-light);
  padding: 16px 20px;
  background: var(--color-bg-page);
}

.preface-empty {
  text-align: center;
  padding: 20px;
  color: var(--color-text-muted);
  font-size: 14px;
  font-family: var(--font-ui);
}
.preface-empty-hint {
  font-size: 12px;
  margin-top: 6px;
}

/* ── Outline Editor Shared ── */
.outline-editor {
  position: relative;
}

.outline-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: #fff;
  color: var(--color-text-primary);
  font-family: var(--font-editor);
  font-size: 14px;
  line-height: 1.7;
  resize: vertical;
  outline: none;
  transition: border-color var(--transition-fast);
}
.outline-textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px rgba(201, 169, 78, 0.12);
}

.outline-save-row {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.save-btn {
  padding: 5px 16px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid var(--color-accent);
  border-radius: 6px;
  background: var(--color-accent);
  color: #fff;
  cursor: pointer;
  font-family: var(--font-ui);
  transition: all var(--transition-fast);
}
.save-btn:hover {
  background: var(--color-accent-light);
  border-color: var(--color-accent-light);
}

.outline-mode-toggle {
  display: flex;
  gap: 4px;
  margin-top: 8px;
}

.mode-btn {
  padding: 2px 10px;
  font-size: 11px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: #fff;
  color: var(--color-text-muted);
  cursor: pointer;
  font-family: var(--font-ui);
  transition: all var(--transition-fast);
}
.mode-btn.active {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
  background: rgba(201, 169, 78, 0.08);
}

/* ── Volumes Container ── */
.volumes-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Volume Card ── */
.volume-card {
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  animation: fade-in-up 0.5s ease both;
  animation-delay: var(--v-delay, 0s);
  transition: box-shadow var(--transition-base);
}
.volume-card:hover {
  box-shadow: var(--shadow-md);
}

.volume-header {
  padding: 20px 24px 0;
}

.volume-header-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.volume-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}

.volume-number {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--color-accent);
  line-height: 1;
  opacity: 0.5;
  letter-spacing: 2px;
}

.volume-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: 1px;
}

.volume-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.volume-stat {
  display: flex;
  align-items: baseline;
  gap: 2px;
}
.stat-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: var(--font-display);
}
.stat-label {
  font-size: 12px;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
}

.volume-progress {
  width: 60px;
}

.progress-track {
  height: 4px;
  background: var(--color-border-light);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  border-radius: 2px;
  transition: width var(--transition-slow);
}

.vol-btn {
  padding: 4px 12px;
  font-size: 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: #fff;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-family: var(--font-ui);
  font-weight: 500;
  transition: all var(--transition-fast);
}
.vol-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
}
.vol-btn.active {
  background: rgba(201, 169, 78, 0.08);
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
}

.vol-gen-btn {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
  background: rgba(201, 169, 78, 0.06);
}
.vol-gen-btn:hover {
  background: var(--color-accent);
  color: #fff;
}
.vol-gen-btn.loading {
  opacity: 0.6;
  pointer-events: none;
}

.vol-del-btn {
  color: var(--color-text-muted);
  border-color: transparent;
  background: transparent;
}
.vol-del-btn:hover {
  color: var(--color-error) !important;
  border-color: var(--color-error) !important;
  background: rgba(196, 90, 90, 0.06) !important;
}

.volume-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 6px 0 0 44px;
  line-height: 1.5;
  font-family: var(--font-ui);
}

.vol-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 12px 0 0;
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    var(--color-border) 15%,
    var(--color-border) 85%,
    transparent
  );
  position: relative;
}
.vol-divider-ornament {
  position: absolute;
  font-size: 10px;
  color: var(--color-accent);
  background: #fff;
  padding: 0 12px;
  line-height: 1;
}

/* ── Volume Outline ── */
.volume-outline {
  padding: 12px 24px 16px;
  background: var(--color-bg-page);
  border-bottom: 1px solid var(--color-border-light);
}

.volume-outline-empty {
  text-align: center;
  padding: 12px;
  color: var(--color-text-muted);
  font-size: 13px;
  font-family: var(--font-ui);
}

/* ── Arcs Tree ── */
.arcs-tree {
  padding: 8px 24px 20px;
}

.arc-node {
  display: flex;
  gap: 14px;
  animation: fade-in-up 0.4s ease both;
  animation-delay: var(--a-delay, 0s);
}

.arc-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 12px;
  flex-shrink: 0;
  padding-top: 14px;
}

.arc-line {
  width: 2px;
  flex: 1;
  min-height: 100%;
  background: linear-gradient(to bottom, var(--color-accent), var(--color-border-light));
  opacity: 0.4;
}

.arc-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-accent);
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px var(--color-accent);
  flex-shrink: 0;
  z-index: 1;
}

.arc-dot-muted {
  background: var(--color-text-muted);
  box-shadow: 0 0 0 2px var(--color-text-muted);
}

.arc-content {
  flex: 1;
  min-width: 0;
  padding-bottom: 16px;
}

.arc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin-left: -12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.arc-header:hover {
  background: rgba(201, 169, 78, 0.04);
}

.arc-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.arc-num {
  font-family: var(--font-display);
  font-size: 12px;
  color: var(--color-accent);
  font-weight: 600;
  white-space: nowrap;
}

.arc-title {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: 0.5px;
}

.arc-title-muted {
  color: var(--color-text-muted);
  font-style: italic;
}

.arc-chapter-count {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  padding: 1px 6px;
  background: var(--color-border-light);
  border-radius: 4px;
  white-space: nowrap;
}

.arc-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.arc-btn {
  padding: 3px 10px;
  font-size: 11px;
  border: 1px solid var(--color-border);
  border-radius: 5px;
  background: #fff;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-family: var(--font-ui);
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.arc-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
}
.arc-btn.active {
  background: rgba(201, 169, 78, 0.08);
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
}

.arc-gen-btn {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
  background: rgba(201, 169, 78, 0.06);
}
.arc-gen-btn:hover {
  background: var(--color-accent);
  color: #fff;
}
.arc-gen-btn.loading {
  opacity: 0.6;
  pointer-events: none;
}

.arc-del-btn {
  color: var(--color-text-muted);
  border-color: transparent;
  background: transparent;
}
.arc-del-btn:hover {
  color: var(--color-error) !important;
  border-color: var(--color-error) !important;
  background: rgba(196, 90, 90, 0.06) !important;
}

.arc-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 2px 0 8px 0;
  line-height: 1.5;
  font-family: var(--font-ui);
  padding: 0 12px;
}

/* Arc Outline */
.arc-outline-section {
  padding: 10px 12px;
  margin: 6px 0 10px;
  background: var(--color-bg-page);
  border-radius: 8px;
  border: 1px solid var(--color-border-light);
}

.arc-outline-empty {
  text-align: center;
  padding: 8px;
  color: var(--color-text-muted);
  font-size: 12px;
  font-family: var(--font-ui);
}

/* ── Chapter List ── */
.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 4px 0;
}

.chapter-card {
  display: flex;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  background: #fff;
  transition: all var(--transition-fast);
  animation: fade-in-up 0.35s ease both;
  animation-delay: var(--c-delay, 0s);
}
.chapter-card:hover {
  border-color: var(--color-accent);
  box-shadow: 0 4px 12px rgba(201, 169, 78, 0.1);
  transform: translateX(3px);
}
.chapter-card:active {
  transform: translateX(1px);
}

.chapter-strip {
  width: 4px;
  flex-shrink: 0;
  background: var(--color-border);
  transition: background var(--transition-base);
}
.chapter-card.status-pending .chapter-strip {
  background: var(--color-accent);
}
.chapter-card.status-generating .chapter-strip {
  background: var(--color-warning);
}
.chapter-card.status-completed .chapter-strip {
  background: var(--color-success);
}

.chapter-inner {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  min-width: 0;
}

.chapter-main {
  flex: 1;
  min-width: 0;
}

.chapter-title {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 2px;
  letter-spacing: 0.3px;
}

.chapter-summary {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  font-family: var(--font-ui);
}

.chapter-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
  min-width: 60px;
}

.chapter-status-tag {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: var(--font-ui);
}
.tag-pending {
  background: rgba(201, 169, 78, 0.1);
  color: var(--color-accent-dark);
}
.tag-generating {
  background: rgba(212, 167, 78, 0.1);
  color: var(--color-warning);
}
.tag-completed {
  background: rgba(106, 171, 122, 0.1);
  color: var(--color-success);
}

.chapter-wordcount {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  white-space: nowrap;
}

.chapter-actions {
  display: flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.chapter-card:hover .chapter-actions {
  opacity: 1;
}

.ch-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  font-size: 11px;
  border: 1px solid var(--color-border);
  border-radius: 5px;
  background: #fff;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-family: var(--font-ui);
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.ch-action-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
  background: rgba(201, 169, 78, 0.06);
}

.ch-action-icon {
  font-size: 9px;
  line-height: 1;
}

.ch-action-danger:hover {
  border-color: var(--color-error) !important;
  color: var(--color-error) !important;
  background: rgba(196, 90, 90, 0.06) !important;
}

.chapter-empty {
  text-align: center;
  padding: 12px;
  color: var(--color-text-muted);
  font-size: 12px;
  font-family: var(--font-ui);
}

/* ── Empty State ── */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  animation: fade-in-up 0.6s ease both;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  line-height: 1;
}

.empty-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 8px;
  letter-spacing: 1px;
}

.empty-desc {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0 0 24px;
  font-family: var(--font-ui);
}

.empty-cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  background: var(--color-accent);
  color: #fff;
  cursor: pointer;
  font-family: var(--font-ui);
  transition: all var(--transition-fast);
  box-shadow: 0 2px 8px rgba(201, 169, 78, 0.3);
}
.empty-cta:hover {
  background: var(--color-accent-light);
  box-shadow: 0 4px 16px rgba(201, 169, 78, 0.4);
  transform: translateY(-1px);
}

/* ── Markdown Body ── */
.markdown-body {
  padding: 12px 16px;
  background: #fff;
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  font-family: var(--font-editor);
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-primary);
  overflow-x: auto;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  font-family: var(--font-display);
  font-weight: 600;
  margin: 0.8em 0 0.4em;
  color: var(--color-accent-dark);
}
.markdown-body :deep(h1) { font-size: 1.35em; }
.markdown-body :deep(h2) { font-size: 1.2em; }
.markdown-body :deep(h3) { font-size: 1.1em; }
.markdown-body :deep(p) { margin: 0 0 0.5em; }
.markdown-body :deep(ul),
.markdown-body :deep(ol) { padding-left: 1.5em; margin: 0.3em 0; }
.markdown-body :deep(li) { margin: 0.15em 0; }
.markdown-body :deep(strong) { font-weight: 600; }
.markdown-body :deep(code) {
  background: rgba(201, 169, 78, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
}
.markdown-body :deep(pre) {
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
}
.markdown-body :deep(pre code) { background: none; padding: 0; }
.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 1em 0;
}
.markdown-body :deep(blockquote) {
  border-left: 3px solid var(--color-accent);
  margin: 0.4em 0;
  padding: 4px 12px;
  color: var(--color-text-secondary);
  background: rgba(201, 169, 78, 0.04);
  border-radius: 0 4px 4px 0;
}
.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--color-border);
  padding: 6px 10px;
  text-align: left;
}
.markdown-body :deep(th) {
  background: var(--color-bg-page);
  font-weight: 600;
}

/* ── Generation Modal ── */
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
  font-family: var(--font-ui);
}
.gen-text {
  white-space: pre-wrap;
  font-family: var(--font-editor);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* ── Transitions ── */
.outline-slide-enter-active {
  transition: all 0.25s ease-out;
  overflow: hidden;
}
.outline-slide-leave-active {
  transition: all 0.15s ease-in;
  overflow: hidden;
}
.outline-slide-enter-from,
.outline-slide-leave-to {
  opacity: 0;
  max-height: 0;
}
.outline-slide-enter-to,
.outline-slide-leave-from {
  max-height: 2000px;
}

/* ── Spin animation ── */
@keyframes spin {
  to { transform: rotate(360deg); }
}
.spin {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .toolbar-right {
    flex-wrap: wrap;
  }
  .volume-header-top {
    flex-direction: column;
  }
  .volume-header-actions {
    margin-left: 44px;
  }
  .chapter-inner {
    flex-direction: column;
    gap: 8px;
  }
  .chapter-side {
    flex-direction: row;
    align-items: center;
  }
  .chapter-actions {
    opacity: 1;
  }
}
</style>
