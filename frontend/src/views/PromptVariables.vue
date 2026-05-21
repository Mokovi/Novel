<template>
  <div class="prompt-variables">
    <!-- Header -->
    <div class="page-header">
      <h2>提示词变量</h2>
      <div class="header-actions">
        <n-button size="small" quaternary @click="handleRefresh">
          <template #icon>
            <n-icon>
              <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </n-icon>
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
          <div v-for="v in bookVariables" :key="v.name" class="enhanced-card card-accent-gold">
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
                <div v-if="previewStates[v.name]" class="preview-wrapper">
                  <CopyButton :text="editValues[v.name]" />
                  <div class="markdown-preview" v-html="renderMarkdown(editValues[v.name])" />
                </div>
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
          <SectionHeader title="世界观设定" tag="worldview">
            <n-button size="small" quaternary @click="handleRefreshWorldview">
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </n-icon>
              </template>
            </n-button>
            <n-button size="small" @click="worldviewGen.prepare()">
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="currentColor" stroke-width="2" fill="none"/></svg>
                </n-icon>
              </template>
              AI 生成设定
            </n-button>
            <n-button size="small" type="primary" :loading="worldviewSaving" @click="handleSaveWorldview">保存</n-button>
          </SectionHeader>

          <div class="editor-mode-bar">
            <button class="mode-btn" :class="{ active: worldviewPreview }" @click="worldviewPreview = true">预览</button>
            <button class="mode-btn" :class="{ active: !worldviewPreview }" @click="worldviewPreview = false">编辑</button>
          </div>
          <template v-if="worldviewPreview">
            <div class="preview-wrapper full-width-preview">
              <CopyButton :text="worldviewText" />
              <div class="markdown-preview" v-html="renderMarkdown(worldviewText)" />
            </div>
          </template>
          <textarea v-else v-model="worldviewText" class="markdown-textarea worldview-textarea" placeholder="在此输入世界观设定（支持 Markdown 格式）&#10;&#10;可以使用 ## 标题、- 列表、**加粗** 等格式" />

          <GenModal
            title="AI 生成世界观设定"
            gen-type="worldview"
            :visible="worldviewGen.visible.value"
            :phase="worldviewGen.phase.value"
            :output="worldviewGen.output.value"
            :model="worldviewGen.model.value"
            :tokens="worldviewGen.tokens.value"
            :running="worldviewGen.running.value"
            :injection-items="worldviewGen.injectionItems.value"
            :book-id="bookId"
            @start="worldviewGen.start"
            @cancel="worldviewGen.cancel()"
            @close="worldviewGen.close()"
          />
        </div>
      </n-tab-pane>

      <!-- ═══ 地点 ═══ -->
      <n-tab-pane name="map" tab="地点">
        <div class="character-section">
          <SectionHeader title="地点管理" tag="map_data">
            <n-button size="small" quaternary @click="fetchLocations">
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </n-icon>
              </template>
              刷新
            </n-button>
            <n-button size="small" @click="locGen.prepare()">
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="currentColor" stroke-width="2" fill="none"/></svg>
                </n-icon>
              </template>
              AI 生成设定
            </n-button>
            <n-button type="primary" size="small" @click="showCreateLoc = true">
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                </n-icon>
              </template>
              新建地点
            </n-button>
          </SectionHeader>

          <div class="filter-bar">
            <n-radio-group v-model:value="locTypeFilter" size="small">
              <n-radio-button value="">全部</n-radio-button>
              <n-radio-button value="continent">大陆</n-radio-button>
              <n-radio-button value="country">国家</n-radio-button>
              <n-radio-button value="city">城市</n-radio-button>
              <n-radio-button value="landmark">地标</n-radio-button>
              <n-radio-button value="region">区域</n-radio-button>
            </n-radio-group>
          </div>
          <div v-if="locLoading" class="loading-center"><n-spin size="medium" /></div>
          <n-empty v-else-if="locations.length === 0" description="暂无地点，点击「新建地点」开始创建" class="empty-state" />
          <div v-else class="card-grid">
            <n-card v-for="loc in filteredLocations" :key="loc.id" class="enhanced-card character-card" hoverable size="small">
              <div class="card-content">
                <div class="card-top">
                  <span class="character-name">{{ loc.name }}</span>
                  <n-tag v-if="loc.location_type" :type="locTypeColors[loc.location_type] || 'default'" size="tiny">{{ locTypeLabels[loc.location_type] || loc.location_type }}</n-tag>
                </div>
                <div class="card-desc">{{ loc.description || '暂无描述' }}</div>
                <div class="card-footer">
                  <span class="card-time">{{ formatDate(loc.updated_at) }}</span>
                </div>
              </div>
            </n-card>
          </div>

          <!-- Create location modal -->
          <n-modal v-model:show="showCreateLoc" preset="card" title="新建地点" style="width: 480px" segmented>
            <n-space vertical>
              <n-input v-model:value="newLocName" placeholder="地点名称" />
              <n-select v-model:value="newLocType" placeholder="地点类型" :options="[
                { label: '大陆', value: 'continent' },
                { label: '国家', value: 'country' },
                { label: '城市', value: 'city' },
                { label: '地标', value: 'landmark' },
                { label: '区域', value: 'region' },
              ]" clearable />
              <n-input v-model:value="newLocDesc" type="textarea" rows="4" placeholder="地点描述" />
            </n-space>
            <template #footer>
              <n-space justify="end">
                <n-button size="small" @click="showCreateLoc = false">取消</n-button>
                <n-button size="small" type="primary" @click="handleCreateLocation">确认</n-button>
              </n-space>
            </template>
          </n-modal>

          <GenModal
            title="AI 生成地图设定"
            gen-type="map"
            :visible="locGen.visible.value"
            :phase="locGen.phase.value"
            :output="locGen.output.value"
            :model="locGen.model.value"
            :tokens="locGen.tokens.value"
            :running="locGen.running.value"
            :injection-items="locGen.injectionItems.value"
            :book-id="bookId"
            @start="locGen.start"
            @cancel="locGen.cancel()"
            @close="locGen.close()"
          />
        </div>
      </n-tab-pane>

      <!-- ═══ 人物 ═══ -->
      <n-tab-pane name="characters" tab="人物">
        <div class="character-section">
          <SectionHeader title="人物管理" tag="character_profiles">
            <n-button size="small" quaternary @click="handleExportCharacters">
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </n-icon>
              </template>
              导出
            </n-button>
            <n-button size="small" quaternary @click="handleImportClick">
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </n-icon>
              </template>
              导入
            </n-button>
            <n-button size="small" @click="charGen.prepare()">
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="currentColor" stroke-width="2" fill="none"/></svg>
                </n-icon>
              </template>
              AI 生成人物
            </n-button>
            <n-button type="primary" size="small" @click="showCreateChar = true">
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                </n-icon>
              </template>
              新建人物
            </n-button>
          </SectionHeader>

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
            <n-card v-for="c in characters" :key="c.id" class="enhanced-card character-card" hoverable size="small" @click="openCharDetail(c.id)">
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

          <GenModal
            title="AI 生成人物"
            gen-type="character"
            :visible="charGen.visible.value"
            :phase="charGen.phase.value"
            :output="charGen.output.value"
            :model="charGen.model.value"
            :tokens="charGen.tokens.value"
            :running="charGen.running.value"
            :injection-items="charGen.injectionItems.value"
            :result="charGen.result.value"
            :book-id="bookId"
            @start="charGen.start"
            @cancel="charGen.cancel()"
            @close="charGen.close()"
          />
        </div>
      </n-tab-pane>

      <!-- ═══ 上下文变量 ═══ -->
      <n-tab-pane name="context" tab="上下文变量">
        <div v-if="loading" class="loading-center"><n-spin size="medium" /></div>
        <div v-else class="variable-list">
          <div v-for="v in contextVariables" :key="v.name" class="enhanced-card card-accent-muted">
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
          <div v-for="v in derivedVariables" :key="v.name" class="enhanced-card card-accent-muted">
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
import { listLocations, createLocation } from '../api/locations.js'
import { listCharacters, importCharacters } from '../api/characters.js'
import { generateWorldview, fetchWorldviewInjections, generateMap, fetchMapInjections, generateCharacters, fetchCharacterInjections } from '../api/generate.js'
import CharacterForm from '../components/character/CharacterForm.vue'
import SectionHeader from '../components/common/SectionHeader.vue'
import CopyButton from '../components/common/CopyButton.vue'
import GenModal from '../components/generate/GenModal.vue'
import { useSSEGeneration } from '../composables/useSSEGeneration.js'

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

// ── Locations tab state ──
const locations = ref([])
const locLoading = ref(false)
const locTypeFilter = ref('')
const showCreateLoc = ref(false)
const newLocName = ref('')
const newLocType = ref('')
const newLocDesc = ref('')

// ── SSE Generation composables ──
const worldviewGen = useSSEGeneration({
  genType: 'worldview',
  bookId,
  fetchInjectionsFn: fetchWorldviewInjections,
  generateFn: generateWorldview,
  onReload: () => {
    worldviewLoaded.value = false
    loadWorldview()
  },
})

const locGen = useSSEGeneration({
  genType: 'map',
  bookId,
  fetchInjectionsFn: fetchMapInjections,
  generateFn: generateMap,
  onReload: fetchLocations,
})

const charGen = useSSEGeneration({
  genType: 'character',
  bookId,
  fetchInjectionsFn: fetchCharacterInjections,
  generateFn: generateCharacters,
  onReload: fetchCharacters,
})

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

const locTypeLabels = {
  continent: '大陆', country: '国家', city: '城市',
  landmark: '地标', region: '区域',
}
const locTypeColors = {
  continent: 'geekblue', country: 'purple', city: 'cyan',
  landmark: 'orange', region: 'default',
}

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

async function fetchLocations() {
  locLoading.value = true
  try {
    const res = await listLocations(bookId.value)
    locations.value = res.data || []
  } catch { message.error('加载地点列表失败') }
  finally { locLoading.value = false }
}

async function handleCreateLocation() {
  if (!newLocName.value.trim()) {
    message.warning('请输入地点名称')
    return
  }
  try {
    await createLocation({
      name: newLocName.value.trim(),
      location_type: newLocType.value || null,
      description: newLocDesc.value || null,
    }, bookId.value)
    message.success('地点创建成功')
    showCreateLoc.value = false
    newLocName.value = ''
    newLocType.value = ''
    newLocDesc.value = ''
    await fetchLocations()
  } catch (e) {
    message.error('创建失败: ' + (e.response?.data?.detail || e.message))
  }
}

const filteredLocations = computed(() => {
  if (!locTypeFilter.value) return locations.value
  return locations.value.filter(l => l.location_type === locTypeFilter.value)
})

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
  if (tab === 'map' && locations.value.length === 0) fetchLocations()
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

async function handleRefreshWorldview() {
  worldviewLoaded.value = false
  await loadWorldview()
  message.success('已刷新')
}

// ── Character import/export handlers ──
async function handleExportCharacters() {
  const data = characters.value.map(c => ({
    name: c.name,
    aliases: c.aliases || null,
    role_type: c.role_type || null,
    status: c.status || 'active',
    description: c.description || null,
    appearance: c.appearance || null,
    personality: c.personality || null,
    background: c.background || null,
    goals: c.goals || null,
  }))
  const blob = new Blob(
    [JSON.stringify({ format_version: 1, characters: data }, null, 2)],
    { type: 'application/json' },
  )

  if ('showSaveFilePicker' in window) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: `characters_${bookId.value}.json`,
        types: [{ description: 'JSON 文件', accept: { 'application/json': ['.json'] } }],
      })
      const writable = await handle.createWritable()
      await writable.write(blob)
      await writable.close()
      message.success('导出成功')
      return
    } catch (err) {
      if (err.name === 'AbortError' || err.name === 'SecurityError') return
      console.warn('showSaveFilePicker failed, falling back to download:', err)
    }
  }

  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `characters_${bookId.value}.json`
  a.click()
  URL.revokeObjectURL(url)
  message.success('导出成功')
}

function handleImportClick() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.style.display = 'none'
  input.addEventListener('change', handleFileSelected)
  document.body.appendChild(input)
  input.click()
  document.body.removeChild(input)
}

async function handleFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  try {
    const text = await file.text()
    const data = JSON.parse(text)
    if (!data.characters || !Array.isArray(data.characters)) {
      message.error('无效的导入文件：缺少 characters 数组')
      return
    }
    const res = await importCharacters(bookId.value, data)
    const result = res.data
    if (result.errors?.length) {
      message.warning(`导入完成，${result.created_count} 条成功，${result.skipped_count} 条跳过`)
      console.warn('Import errors:', result.errors)
    } else {
      message.success(`成功导入 ${result.created_count} 个人物`)
    }
    await fetchCharacters()
  } catch (err) {
    message.error('导入失败: ' + (err.response?.data?.detail || err.message))
  }
}

async function handleRefresh() {
  await loadVariables()
  worldviewLoaded.value = false
  if (activeTab.value === 'worldview') await loadWorldview()
  if (activeTab.value === 'map') await fetchLocations()
  if (activeTab.value === 'characters') await fetchCharacters()
  message.success('已刷新')
}

onMounted(() => {
  loadVariables()
  if (route.query.tab === 'worldview') loadWorldview()
  if (route.query.tab === 'map') fetchLocations()
  if (route.query.tab === 'characters') fetchCharacters()
})
</script>

<style scoped>
.prompt-variables { max-width: 960px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px; }
.page-header h2 { margin: 0; font-family: var(--font-display); font-size: 28px; font-weight: 700; color: var(--color-text-primary); position: relative; }
.page-header h2::after { content: ''; display: block; width: 40px; height: 3px; border-radius: 2px; background: var(--color-accent); margin-top: 6px; }
.header-actions { display: flex; gap: 8px; }
.loading-center { display: flex; justify-content: center; align-items: center; min-height: 200px; }

/* ── Enhanced Cards ── */
.enhanced-card {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-bg-card);
  padding: 24px;
  box-shadow: var(--shadow-card-rest);
  transition: var(--transition-card);
  animation: fade-in-up 0.35s ease both;
}
.enhanced-card:hover {
  box-shadow: var(--shadow-card-lift);
  transform: translateY(-2px);
}
.enhanced-card:nth-child(2) { animation-delay: 0.05s; }
.enhanced-card:nth-child(3) { animation-delay: 0.1s; }
.enhanced-card:nth-child(4) { animation-delay: 0.15s; }
.enhanced-card:nth-child(5) { animation-delay: 0.2s; }
.enhanced-card:nth-child(6) { animation-delay: 0.25s; }

.card-accent-gold { border-left: 3px solid var(--color-accent); }
.card-accent-success { border-left: 3px solid var(--color-success); }
.card-accent-muted { border-left: 3px solid var(--color-text-muted); }
.card-accent-info { border-left: 3px solid var(--color-info); }

.variable-list { display: flex; flex-direction: column; gap: 20px; }
.card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.var-label { font-size: 15px; font-weight: 600; color: var(--color-text-primary); }
.var-name-tag {
  font-size: 11px; padding: 2px 8px; border-radius: 4px;
  background: #e8e6e1; color: #666;
  font-family: var(--font-mono, monospace);
}
.var-name-tag.readonly { background: #f0f0ee; color: #999; }
.card-body { min-height: 32px; }
.card-actions { display: flex; justify-content: flex-end; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--color-border); }
.readonly-value { padding: 8px 0; }
.help-text { font-size: 13px; line-height: 1.6; }
.json-error {
  font-size: 12px; color: #d03050; margin-bottom: 6px; padding: 4px 8px;
  background: #fff0f0; border-radius: 4px; white-space: pre-wrap; word-break: break-word;
}

/* ── Markdown editor ── */
.markdown-textarea {
  width: 100%; min-height: 200px; padding: 16px;
  border: 1px solid var(--color-border); border-radius: 8px;
  font-family: var(--font-mono, 'SF Mono', 'Fira Code', monospace);
  font-size: 14px; line-height: 1.8; color: var(--color-text-primary);
  background: var(--color-bg-editor); resize: vertical; outline: none; box-sizing: border-box;
}
.markdown-textarea:focus { border-color: var(--color-accent); box-shadow: 0 0 0 2px rgba(201, 169, 78, 0.12); }
.markdown-textarea::placeholder { color: var(--color-text-muted); opacity: 0.5; }
.worldview-textarea { min-height: 500px; }
.editor-mode-bar {
  display: flex; gap: 0; margin-bottom: 16px;
  border: 1px solid var(--color-border); border-radius: 6px; overflow: hidden; align-self: flex-start;
}
.mode-btn {
  padding: 4px 16px; font-size: 12px; font-family: var(--font-ui);
  border: none; cursor: pointer; background: transparent; color: var(--color-text-muted);
}
.mode-btn.active { background: var(--color-accent); color: #fff; }
.mode-btn:not(.active):hover { background: var(--color-bg-hover, #f0f0f0); }
.markdown-preview {
  min-height: 200px; padding: 20px; border: 1px solid var(--color-border);
  border-radius: 8px; background: #fafaf8; font-size: 14px; line-height: 1.8;
  color: var(--color-text-primary); overflow-y: auto;
}

/* ── Preview wrapper (hosts CopyButton) ── */
.preview-wrapper {
  position: relative;
}
.full-width-preview {
  position: relative;
  margin-bottom: 20px;
}

/* ── Worldview section ── */
.worldview-section { min-height: 400px; }

/* ── Character section ── */
.character-section { min-height: 400px; }
.filter-bar { margin-bottom: 20px; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
.character-card { cursor: pointer; border-left: 3px solid var(--color-accent); }
.card-content { display: flex; flex-direction: column; gap: 6px; }
.card-top { display: flex; justify-content: space-between; align-items: center; }
.character-name { font-size: 16px; font-weight: 600; color: var(--color-text-primary); }
.card-aliases { font-size: 12px; color: var(--color-text-muted); }
.card-desc { font-size: 13px; color: #666; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5; }
.card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
.card-time { font-size: 11px; color: var(--color-text-muted); }
.empty-state { min-height: 200px; display: flex; align-items: center; justify-content: center; }
</style>
