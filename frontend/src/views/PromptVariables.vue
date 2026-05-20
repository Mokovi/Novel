<template>
  <div class="prompt-variables">
    <!-- Header -->
    <div class="page-header">
      <h2>提示词变量</h2>
      <div class="header-actions">
        <n-button size="small" quaternary @click="handleRefresh">
          <template #icon>
            <n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></n-icon>
          </template>
          刷新
        </n-button>
      </div>
    </div>

    <!-- Category tabs -->
    <n-tabs v-model:value="activeTab" type="line" animated>
      <!-- ═══ 书籍变量 ═══ -->
      <n-tab-pane name="book" tab="书籍变量">
        <div v-if="loading" class="loading-center"><n-spin size="medium" /></div>
        <div v-else class="variable-list">
          <div v-for="v in bookVariables" :key="v.name" class="variable-card">
            <div class="card-header">
              <span class="var-label">{{ v.label }}</span>
              <span class="var-name-tag">{{ v.name }}</span>
            </div>
            <div class="card-body">
              <template v-if="v.editor === 'input'">
                <n-input v-model:value="editValues[v.name]" :placeholder="'输入' + v.label" @keyup.enter="handleSave(v)" />
              </template>
              <template v-else-if="v.editor === 'textarea_3'">
                <n-input v-model:value="editValues[v.name]" type="textarea" :rows="3" :placeholder="'输入' + v.label" />
              </template>
              <template v-else-if="v.editor === 'markdown'">
                <div class="editor-mode-bar">
                  <button class="mode-btn" :class="{ active: previewStates[v.name] }" @click="previewStates[v.name] = true">预览</button>
                  <button class="mode-btn" :class="{ active: !previewStates[v.name] }" @click="previewStates[v.name] = false">编辑</button>
                </div>
                <div v-if="previewStates[v.name]" class="markdown-preview" v-html="renderMarkdown(editValues[v.name])" />
                <textarea v-else v-model="editValues[v.name]" class="markdown-textarea" :placeholder="'输入' + v.label + '（支持 Markdown 格式）'" />
              </template>
              <template v-else-if="v.editor === 'json'">
                <div v-if="jsonErrors[v.name]" class="json-error">{{ jsonErrors[v.name] }}</div>
                <n-input v-model:value="editValues[v.name]" type="textarea" :rows="8" placeholder="输入 JSON 格式的写作风格配置" :status="jsonErrors[v.name] ? 'error' : undefined" @update:value="() => validateJson(v.name)" />
              </template>
            </div>
            <div v-if="v.editable" class="card-actions">
              <n-button size="tiny" :loading="savingStates[v.name]" :disabled="jsonErrors[v.name] !== null" @click="handleSave(v)">保存</n-button>
            </div>
          </div>
        </div>
      </n-tab-pane>

      <!-- ═══ 世界观 ═══ -->
      <n-tab-pane name="worldview" tab="世界观">
        <div class="worldview-section">
          <div class="section-header">
            <h3>世界观设定 <span class="var-name-tag" style="margin-left:8px">worldview</span></h3>
            <div class="header-actions">
              <n-button size="small" quaternary @click="handleRefreshWorldview">
                <template #icon>
                  <n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></n-icon>
                </template>
              </n-button>
              <n-button size="small" @click="prepareGenerateWorldview">
                <template #icon>
                  <n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="currentColor" stroke-width="2" fill="none"/></svg></n-icon>
                </template>
                AI 生成设定
              </n-button>
              <n-button size="small" type="primary" :loading="worldviewSaving" @click="handleSaveWorldview">保存</n-button>
            </div>
          </div>
          <div class="editor-mode-bar">
            <button class="mode-btn" :class="{ active: worldviewPreview }" @click="worldviewPreview = true">预览</button>
            <button class="mode-btn" :class="{ active: !worldviewPreview }" @click="worldviewPreview = false">编辑</button>
          </div>
          <div v-if="worldviewPreview" class="markdown-preview" v-html="renderMarkdown(worldviewText)" />
          <textarea v-else v-model="worldviewText" class="markdown-textarea worldview-textarea" placeholder="在此输入世界观设定（支持 Markdown 格式）&#10;&#10;可以使用 ## 标题、- 列表、**加粗** 等格式" />
        </div>

        <!-- ═══ SSE Generation Modal ═══ -->
        <n-modal v-model:show="showGenModal" :mask-closable="false" style="width: 720px">
          <n-card title="AI 生成世界观设定" style="max-height: 80vh; overflow-y: auto; border-radius: 12px">
            <div v-if="genPhase === 'idle'">
              <PromptInjectionPanel
                title="AI 生成世界观设定"
                :injection-items="injectionItems"
                :book-id="bookId"
                :loading="genRunning"
                gen-type="worldview"
                @start="startWorldviewGen"
                @cancel="showGenModal = false"
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
                <template v-if="genPhase === 'generating'">
                  <n-button @click="cancelGeneration">取消</n-button>
                </template>
                <template v-else-if="genPhase === 'done'">
                  <n-button type="primary" @click="closeGenModal">关闭</n-button>
                </template>
              </n-space>
            </template>
          </n-card>
        </n-modal>
      </n-tab-pane>

      <!-- ═══ 人物 ═══ -->
      <n-tab-pane name="characters" tab="人物">
        <div class="character-section">
          <div class="section-header">
            <h3>人物管理 <span class="var-name-tag" style="margin-left:8px">character_profiles</span></h3>
            <n-button type="primary" size="small" @click="showCreateChar = true">
              <template #icon>
                <n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></n-icon>
              </template>
              新建人物
            </n-button>
          </div>
          <div class="filter-bar">
            <n-radio-group v-model:value="charRoleFilter" size="small" @update:value="fetchCharacters">
              <n-radio-button value="">全部</n-radio-button>
              <n-radio-button value="protagonist">主角</n-radio-button>
              <n-radio-button value="antagonist">反派</n-radio-button>
              <n-radio-button value="supporting">配角</n-radio-button>
              <n-radio-button value="minor">龙套</n-radio-button>
            </n-radio-group>
          </div>
          <div v-if="charLoading" class="loading-center"><n-spin size="medium" /></div>
          <n-empty v-else-if="characters.length === 0" description="暂无人物，点击「新建人物」开始创建" class="empty-state" />
          <div v-else class="card-grid">
            <n-card v-for="c in characters" :key="c.id" class="character-card" hoverable size="small" @click="openCharDetail(c.id)">
              <div class="card-content">
                <div class="card-top">
                  <span class="character-name">{{ c.name }}</span>
                  <n-tag v-if="c.role_type" :type="charRoleTag(c.role_type)" size="tiny">{{ charRoleLabel(c.role_type) }}</n-tag>
                </div>
                <div v-if="c.aliases" class="card-aliases">{{ c.aliases }}</div>
                <div class="card-desc">{{ c.description || '暂无描述' }}</div>
                <div class="card-footer">
                  <n-tag v-if="c.status === 'active'" size="tiny" type="success">活跃</n-tag>
                  <n-tag v-else-if="c.status === 'deceased'" size="tiny" type="error">已故</n-tag>
                  <n-tag v-else size="tiny" type="warning">{{ c.status }}</n-tag>
                  <span class="card-time">{{ formatDate(c.updated_at) }}</span>
                </div>
              </div>
            </n-card>
          </div>
          <!-- Create character modal -->
          <n-modal v-model:show="showCreateChar" preset="card" title="新建人物" style="width: 520px" segmented>
            <CharacterForm :book-id="bookId" @saved="onCharCreated" @cancel="showCreateChar = false" />
          </n-modal>
        </div>
      </n-tab-pane>

      <!-- ═══ 上下文变量 ═══ -->
      <n-tab-pane name="context" tab="上下文变量">
        <div v-if="loading" class="loading-center"><n-spin size="medium" /></div>
        <div v-else class="variable-list">
          <div v-for="v in contextVariables" :key="v.name" class="variable-card">
            <div class="card-header">
              <span class="var-label">{{ v.label }}</span>
              <span class="var-name-tag readonly">{{ v.name }}</span>
            </div>
            <div class="card-body">
              <div class="readonly-value"><n-text depth="3" class="help-text">{{ v.help_text }}</n-text></div>
            </div>
          </div>
        </div>
      </n-tab-pane>

      <!-- ═══ 衍生变量 ═══ -->
      <n-tab-pane name="derived" tab="衍生变量">
        <div v-if="loading" class="loading-center"><n-spin size="medium" /></div>
        <div v-else class="variable-list">
          <div v-for="v in derivedVariables" :key="v.name" class="variable-card">
            <div class="card-header">
              <span class="var-label">{{ v.label }}</span>
              <span class="var-name-tag readonly">{{ v.name }}</span>
            </div>
            <div class="card-body">
              <div class="readonly-value"><n-text depth="3" class="help-text">{{ v.help_text }}</n-text></div>
            </div>
          </div>
        </div>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { NCard, NSpace } from 'naive-ui'
import { marked } from 'marked'
import { fetchPromptVariables, getBook, updateBook, updateBookWorldview, updateBookOutline, getBookWorldview } from '../api/books.js'
import { listCharacters } from '../api/characters.js'
import { generateWorldview, fetchWorldviewInjections } from '../api/generate.js'
import CharacterForm from '../components/character/CharacterForm.vue'
import PromptInjectionPanel from '../components/generate/PromptInjectionPanel.vue'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const bookId = computed(() => Number(route.params.bookId))

// ── Tab routing ──
const activeTab = ref(route.query.tab || 'book')
watch(activeTab, (val) => {
  router.replace({ query: { ...route.query, tab: val } })
})

// ── Variables state ──
const loading = ref(false)
const variables = ref([])
const editValues = reactive({})
const savingStates = reactive({})
const previewStates = reactive({})
const jsonErrors = reactive({})

const bookVariables = computed(() => variables.value.filter(v => v.category === 'book'))
const contextVariables = computed(() => variables.value.filter(v => v.category === 'context'))
const derivedVariables = computed(() => variables.value.filter(v => v.category === 'derived'))

// ── Worldview tab state ──
const worldviewText = ref('')
const worldviewPreview = ref(true)
const worldviewSaving = ref(false)
const worldviewLoaded = ref(false)

// ── Characters tab state ──
const characters = ref([])
const charLoading = ref(false)
const charRoleFilter = ref('')
const showCreateChar = ref(false)

// ── Worldview generation state ──
const showGenModal = ref(false)
const genOutput = ref('')
const genModel = ref('')
const genTokens = ref(0)
const genRunning = ref(false)
const genAbort = ref(null)
const genPhase = ref('idle') // 'idle' | 'generating' | 'done'
const injectionItems = ref([])

// ── Helpers ──
function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch { return text }
}

const charRoleTag = (type) => {
  const map = { protagonist: 'success', antagonist: 'error', supporting: 'info', minor: 'default' }
  return map[type] || 'default'
}
const charRoleLabel = (type) => {
  const map = { protagonist: '主角', antagonist: '反派', supporting: '配角', minor: '龙套' }
  return map[type] || type
}
const formatDate = (d) => d ? new Date(d).toLocaleDateString('zh-CN') : ''

function validateJson(name) {
  const val = editValues[name]
  if (!val || !val.trim()) { jsonErrors[name] = null; return }
  try { JSON.parse(val); jsonErrors[name] = null }
  catch (e) { jsonErrors[name] = `JSON 解析错误: ${e.message}` }
}

// ── Data loading ──
async function loadVariables() {
  loading.value = true
  try {
    const res = await fetchPromptVariables(bookId.value)
    variables.value = res.data.variables || []
    for (const v of variables.value) {
      if (v.editable) {
        editValues[v.name] = v.value
        previewStates[v.name] = false
        savingStates[v.name] = false
        jsonErrors[v.name] = null
      }
    }
  } catch (e) {
    if (e.response?.status !== 404) {
      message.error('加载变量失败: ' + (e.response?.data?.detail || e.message))
    }
  } finally { loading.value = false }
}

async function loadWorldview() {
  if (worldviewLoaded.value) return
  try {
    const res = await getBookWorldview(bookId.value)
    worldviewText.value = res.data.worldview || ''
    worldviewLoaded.value = true
  } catch (e) {
    message.error('加载世界观失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function fetchCharacters() {
  charLoading.value = true
  try {
    const params = {}
    if (charRoleFilter.value) params.role_type = charRoleFilter.value
    const res = await listCharacters(bookId.value, params)
    characters.value = res.data
  } catch { message.error('加载人物列表失败') }
  finally { charLoading.value = false }
}

function openCharDetail(id) {
  router.push(`/books/${bookId.value}/characters/${id}`)
}

function onCharCreated() {
  showCreateChar.value = false
  fetchCharacters()
  message.success('人物创建成功')
}

// ── Tab switch handlers ──
watch(activeTab, (tab) => {
  if (tab === 'worldview' && !worldviewLoaded.value) loadWorldview()
  if (tab === 'characters' && characters.value.length === 0) fetchCharacters()
})

// ── Save handlers ──
async function handleSave(v) {
  const name = v.name
  savingStates[name] = true
  try {
    const bid = bookId.value
    if (name === 'book_name') await updateBook(bid, { name: editValues[name] })
    else if (name === 'book_description') await updateBook(bid, { description: editValues[name] })
    else if (name === 'book_outline') await updateBookOutline(bid, { outline: editValues[name] })
    else if (name === 'worldview') await updateBookWorldview(bid, { worldview: editValues[name] })
    else if (name === 'writing_style') {
      await updateBook(bid, { writing_style: editValues[name] })
    }
    message.success(`${v.label} 已保存`)
  } catch (e) {
    if (name === 'writing_style' && e instanceof SyntaxError) message.error('JSON 格式无效，请检查后重试')
    else message.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally { savingStates[name] = false }
}

async function handleSaveWorldview() {
  worldviewSaving.value = true
  try {
    await updateBookWorldview(bookId.value, { worldview: worldviewText.value })
    message.success('世界观已保存')
  } catch (e) {
    message.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally { worldviewSaving.value = false }
}

// ── Worldview generation handlers ──
async function prepareGenerateWorldview() {
  genOutput.value = ''
  genModel.value = ''
  genTokens.value = 0
  genRunning.value = false
  genPhase.value = 'idle'
  injectionItems.value = []
  showGenModal.value = true
  try {
    const data = await fetchWorldviewInjections(bookId.value)
    injectionItems.value = data.items || []
  } catch (e) {
    console.error('Failed to fetch injection items:', e)
  }
}

function startWorldviewGen(overrides, userPrompt) {
  genPhase.value = 'generating'
  genRunning.value = true

  const body = { user_prompt: userPrompt || '' }
  if (overrides && (overrides.exclude_variables?.length || overrides.extra_variables || overrides.added_character_ids?.length)) {
    body.injection_overrides = overrides
  }

  genAbort.value = generateWorldview(bookId.value, {
    onStart: (evt) => {
      genModel.value = evt.model || ''
      genTokens.value = evt.token_estimate || 0
    },
    onToken: (token) => {
      genOutput.value += token
    },
    onDone: () => {
      genRunning.value = false
      genPhase.value = 'done'
      message.success('世界观设定生成完成')
    },
    onError: (err) => {
      genRunning.value = false
      genPhase.value = 'done'
      message.error(err)
    },
  }, body)
}

function cancelGeneration() {
  genAbort.value?.abort()
  genRunning.value = false
  genPhase.value = 'idle'
  message.info('已取消生成')
}

function closeGenModal() {
  showGenModal.value = false
  loadWorldview()
}

async function handleRefreshWorldview() {
  worldviewLoaded.value = false
  await loadWorldview()
  message.success('已刷新')
}

async function handleRefresh() {
  await loadVariables()
  worldviewLoaded.value = false
  if (activeTab.value === 'worldview') await loadWorldview()
  if (activeTab.value === 'characters') await fetchCharacters()
  message.success('已刷新')
}

onMounted(() => {
  loadVariables()
  if (route.query.tab === 'worldview') loadWorldview()
  if (route.query.tab === 'characters') fetchCharacters()
})
</script>

<style scoped>
.prompt-variables { max-width: 960px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { margin: 0; font-family: var(--font-display); font-size: 22px; font-weight: 700; color: var(--color-text); }
.header-actions { display: flex; gap: 8px; }
.loading-center { display: flex; justify-content: center; align-items: center; min-height: 200px; }

/* ── Variable cards ── */
.variable-list { display: flex; flex-direction: column; gap: 16px; }
.variable-card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-card);
  padding: 16px 20px;
}
.card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.var-label { font-size: 15px; font-weight: 600; color: var(--color-text); }
.var-name-tag {
  font-size: 11px; padding: 1px 8px; border-radius: 4px;
  background: #e8e6e1; color: #666;
  font-family: var(--font-mono, monospace);
}
.var-name-tag.readonly { background: #f0f0ee; color: #999; }
.card-body { min-height: 32px; }
.card-actions { display: flex; justify-content: flex-end; margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee; }
.readonly-value { padding: 8px 0; }
.help-text { font-size: 13px; line-height: 1.6; }
.json-error {
  font-size: 12px; color: #d03050; margin-bottom: 6px; padding: 4px 8px;
  background: #fff0f0; border-radius: 4px; white-space: pre-wrap; word-break: break-word;
}

/* ── Markdown editor ── */
.markdown-textarea {
  width: 100%; min-height: 200px; padding: 16px;
  border: 1px solid var(--color-border); border-radius: 6px;
  font-family: var(--font-mono, 'SF Mono', 'Fira Code', monospace);
  font-size: 14px; line-height: 1.8; color: var(--color-text);
  background: var(--color-bg-editor); resize: vertical; outline: none; box-sizing: border-box;
}
.markdown-textarea:focus { border-color: var(--color-accent); box-shadow: 0 0 0 2px rgba(201, 169, 78, 0.12); }
.markdown-textarea::placeholder { color: var(--color-text-muted); opacity: 0.5; }
.worldview-textarea { min-height: 500px; }
.editor-mode-bar {
  display: flex; gap: 0; margin-bottom: 12px;
  border: 1px solid var(--color-border); border-radius: 6px; overflow: hidden; align-self: flex-start;
}
.mode-btn {
  padding: 4px 16px; font-size: 12px; font-family: var(--font-ui);
  border: none; cursor: pointer; background: transparent; color: var(--color-text-muted);
}
.mode-btn.active { background: var(--color-accent); color: #fff; }
.mode-btn:not(.active):hover { background: var(--color-bg-hover, #f0f0f0); }
.markdown-preview {
  min-height: 200px; padding: 16px; border: 1px solid var(--color-border);
  border-radius: 6px; background: #fafaf8; font-size: 14px; line-height: 1.8;
  color: var(--color-text); overflow-y: auto;
}

/* ── Worldview section ── */
.worldview-section { min-height: 400px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-header h3 { margin: 0; font-family: var(--font-display); font-size: 18px; font-weight: 600; color: var(--color-text); }

/* ── Character section ── */
.character-section { min-height: 400px; }
.filter-bar { margin-bottom: 16px; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.character-card { cursor: pointer; }
.card-content { display: flex; flex-direction: column; gap: 6px; }
.card-top { display: flex; justify-content: space-between; align-items: center; }
.character-name { font-size: 16px; font-weight: 600; color: var(--color-text); }
.card-aliases { font-size: 12px; color: var(--color-text-muted, #999); }
.card-desc { font-size: 13px; color: #666; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5; }
.card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
.card-time { font-size: 11px; color: var(--color-text-muted, #999); }
.empty-state { min-height: 200px; display: flex; align-items: center; justify-content: center; }
</style>
