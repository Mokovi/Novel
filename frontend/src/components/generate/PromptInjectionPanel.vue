<template>
  <div class="inj-panel">
    <!-- ─── Title ─── -->
    <h3 class="inj-title">{{ title }}</h3>
    <p class="inj-desc">配置生成上下文，或直接开始生成</p>

    <!-- ─── System injection items ─── -->
    <div v-if="injectionItems.length" class="inj-section">
      <label class="inj-section-label">上下文变量</label>
      <div class="inj-items">
        <div
          v-for="item in injectionItems"
          :key="item.variable"
          class="inj-item"
        >
          <span
            class="inj-item-toggle"
            :class="{ active: isEnabled(item) && item.available, muted: !item.available || !isEnabled(item) }"
            @click="toggleItem(item)"
          >
            <svg v-if="isEnabled(item) && item.available" width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
          </span>
          <span class="inj-item-label">{{ item.label }}</span>
          <span v-if="!item.available" class="inj-item-hint">(暂无内容)</span>
        </div>
      </div>
    </div>

    <!-- ─── Character selection grid (collapsible) ─── -->
    <div class="inj-section">
      <div class="inj-section-header" @click="charCollapsed = !charCollapsed">
        <span class="inj-section-arrow" :class="{ collapsed: charCollapsed }">▶</span>
        <label class="inj-section-label">添加角色档案</label>
      </div>
      <div v-show="!charCollapsed" class="inj-section-body">

      <!-- Role type filter -->
      <div class="inj-char-filters">
        <button
          v-for="role in roleTypes"
          :key="role.value"
          class="inj-char-filter-btn"
          :class="{ active: charRoleFilter === role.value }"
          @click="charRoleFilter = charRoleFilter === role.value ? '' : role.value"
        >{{ role.label }}</button>
      </div>

      <!-- Search input -->
      <input
        v-model="charSearchQuery"
        type="text"
        class="inj-char-input"
        placeholder="搜索角色名..."
      />

      <!-- Loading state -->
      <div v-if="charLoading" class="inj-char-grid-loading">
        <n-spin size="small" />
      </div>

      <!-- Empty state -->
      <n-empty
        v-else-if="!charLoading && allCharacters.length === 0"
        description="暂无角色，请在角色管理页面创建"
        class="inj-char-empty"
      />

      <!-- Character grid -->
      <template v-else>
        <div v-if="filteredCharacters.length === 0" class="inj-char-no-result">
          未找到匹配角色
        </div>
        <div v-else class="inj-char-grid">
          <div
            v-for="c in filteredCharacters"
            :key="c.id"
            class="inj-char-card"
            :class="{ selected: isCharSelected(c.id) }"
            @click="toggleCharacter(c)"
          >
            <span class="inj-char-card-name">{{ c.name }}</span>
            <span v-if="c.role_type" class="inj-char-card-type">{{ c.role_type }}</span>
          </div>
        </div>
      </template>

      <!-- Selected tags -->
      <div v-if="addedCharacters.length" class="inj-char-tags">
        <span
          v-for="c in addedCharacters"
          :key="c.id"
          class="inj-char-tag"
        >
          {{ c.name }}
          <span v-if="c.role_type" class="inj-char-tag-type">({{ c.role_type }})</span>
          <button class="inj-char-tag-remove" @click="removeCharacter(c.id)">✕</button>
        </span>
      </div>
      </div>
    </div>

    <!-- ─── Location selection grid (collapsible) ─── -->
    <div class="inj-section">
      <div class="inj-section-header" @click="locCollapsed = !locCollapsed">
        <span class="inj-section-arrow" :class="{ collapsed: locCollapsed }">▶</span>
        <label class="inj-section-label">地图档案</label>
      </div>
      <div v-show="!locCollapsed" class="inj-section-body">

      <!-- Location type filter -->
      <div class="inj-char-filters">
        <button
          v-for="t in locTypeFilters"
          :key="t.value"
          class="inj-char-filter-btn"
          :class="{ active: locTypeFilter === t.value }"
          @click="locTypeFilter = locTypeFilter === t.value ? '' : t.value"
        >{{ t.label }}</button>
      </div>

      <!-- Search input -->
      <input
        v-model="locSearchQuery"
        type="text"
        class="inj-char-input"
        placeholder="搜索地点名..."
      />

      <!-- Loading state -->
      <div v-if="locLoading" class="inj-char-grid-loading">
        <n-spin size="small" />
      </div>

      <!-- Empty state -->
      <n-empty
        v-else-if="!locLoading && allLocations.length === 0"
        description="暂无地点，请在 PromptVariables 地图页面创建"
        class="inj-char-empty"
      />

      <!-- Location grid -->
      <template v-else>
        <div v-if="filteredLocations.length === 0" class="inj-char-no-result">
          未找到匹配地点
        </div>
        <div v-else class="inj-char-grid">
          <div
            v-for="loc in filteredLocations"
            :key="loc.id"
            class="inj-char-card"
            :class="{ selected: isLocSelected(loc.id) }"
            @click="toggleLocation(loc)"
          >
            <span class="inj-char-card-name">{{ loc.name }}</span>
            <span v-if="loc.location_type" class="inj-char-card-type">{{ loc.location_type }}</span>
          </div>
        </div>
      </template>

      <!-- Selected tags -->
      <div v-if="addedLocations.length" class="inj-char-tags">
        <span
          v-for="loc in addedLocations"
          :key="loc.id"
          class="inj-char-tag"
        >
          {{ loc.name }}
          <span v-if="loc.location_type" class="inj-char-tag-type">({{ loc.location_type }})</span>
          <button class="inj-char-tag-remove" @click="removeLocation(loc.id)">✕</button>
        </span>
      </div>
      </div>
    </div>

    <!-- ─── User prompt ─── -->
    <div class="inj-section">
      <label class="inj-section-label">补充提示词</label>
      <textarea
        v-model="userPrompt"
        class="inj-prompt-textarea"
        placeholder="补充提示词（可选）：输入对本次生成的特定要求..."
        rows="3"
      />
    </div>

    <!-- ─── Preview modal ─── -->
    <n-modal v-model:show="showPreview" preset="card" title="提示词预览" style="max-width: 800px">
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
          class="inj-preview-textarea"
        />
      </n-space>
    </n-modal>

    <!-- ─── Actions ─── -->
    <div class="inj-actions">
      <button class="inj-btn inj-btn-ghost" @click="handlePreview" :disabled="previewLoading">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        提示词预览
      </button>
    </div>
    <div class="inj-footer">
      <button class="inj-btn inj-btn-cancel" @click="$emit('cancel')">取消</button>
      <button class="inj-btn inj-btn-start" @click="handleStart" :disabled="loading">
        {{ loading ? '生成中...' : '开始生成' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useMessage } from 'naive-ui'
import { listCharacters } from '../../api/characters.js'
import { listLocations } from '../../api/locations.js'
import { previewPrompt, previewArcPrompt, previewVolumePrompt, previewBookPrompt, previewWorldviewPrompt, previewMapPrompt, previewLocationPrompt, previewCharacterPrompt } from '../../api/generate.js'

const props = defineProps({
  title: { type: String, default: 'AI 生成' },
  injectionItems: { type: Array, default: () => [] },
  availableCharacters: { type: Array, default: () => [] },
  bookId: { type: Number, required: true },
  loading: { type: Boolean, default: false },
  /** Gen type: 'chapter' | 'arc' | 'volume' | 'book' | 'worldview' */
  genType: { type: String, default: 'chapter' },
  /** For chapter/arc/volume - the entity id */
  genId: { type: Number, default: null },
  /** Preview function override (if not using built-in) */
  previewFn: { type: Function, default: null },
})

const emit = defineEmits(['start', 'cancel'])

const message = useMessage()

// ── Injection item toggles ──
const enabledMap = ref({})

watch(() => props.injectionItems, (items) => {
  const m = {}
  for (const item of items) {
    m[item.variable] = item.default_enabled !== false
  }
  enabledMap.value = m
}, { immediate: true })

function isEnabled(item) {
  return enabledMap.value[item.variable] !== false
}

function toggleItem(item) {
  enabledMap.value[item.variable] = !enabledMap.value[item.variable]
}

// ── Collapse state for character and location sections ──
const charCollapsed = ref(false)
const locCollapsed = ref(false)

// ── Role type definitions ──
const roleTypes = [
  { label: '全部', value: '' },
  { label: '主角', value: 'protagonist' },
  { label: '反派', value: 'antagonist' },
  { label: '配角', value: 'supporting' },
  { label: '龙套', value: 'minor' },
]

// ── Character grid ──
const allCharacters = ref([])
const charRoleFilter = ref('')
const charSearchQuery = ref('')
const charLoading = ref(false)
const addedCharacters = ref([])

const filteredCharacters = computed(() => {
  let list = allCharacters.value
  if (charRoleFilter.value) {
    list = list.filter(c => c.role_type === charRoleFilter.value)
  }
  if (charSearchQuery.value.trim()) {
    const q = charSearchQuery.value.trim().toLowerCase()
    list = list.filter(c => c.name.toLowerCase().includes(q))
  }
  return list
})

function isCharSelected(id) {
  return addedCharacters.value.some(c => c.id === id)
}

function toggleCharacter(c) {
  const idx = addedCharacters.value.findIndex(ac => ac.id === c.id)
  if (idx >= 0) {
    addedCharacters.value.splice(idx, 1)
  } else {
    addedCharacters.value.push(c)
  }
}

function removeCharacter(id) {
  addedCharacters.value = addedCharacters.value.filter(c => c.id !== id)
}

onMounted(async () => {
  charLoading.value = true
  try {
    const res = await listCharacters(props.bookId, { limit: 200 })
    allCharacters.value = res.data || []
  } catch (e) {
    console.error('Failed to load characters:', e)
  } finally {
    charLoading.value = false
  }

  locLoading.value = true
  try {
    const res = await listLocations(props.bookId, { limit: 200 })
    allLocations.value = res.data || []
  } catch (e) {
    console.error('Failed to load locations:', e)
  } finally {
    locLoading.value = false
  }
})

onUnmounted(() => {
  if (previewTimer) clearTimeout(previewTimer)
  pendingPreviewVersion = 0
})

// ── Location grid ──
const allLocations = ref([])
const locTypeFilter = ref('')
const locSearchQuery = ref('')
const locLoading = ref(false)
const addedLocations = ref([])

const locTypeFilters = computed(() => {
  const types = new Set()
  types.add('')
  for (const loc of allLocations.value) {
    if (loc.location_type) types.add(loc.location_type)
  }
  return Array.from(types).map(t => ({
    label: t || '全部',
    value: t,
  }))
})

const filteredLocations = computed(() => {
  let list = allLocations.value
  if (locTypeFilter.value) {
    list = list.filter(l => l.location_type === locTypeFilter.value)
  }
  if (locSearchQuery.value.trim()) {
    const q = locSearchQuery.value.trim().toLowerCase()
    list = list.filter(l => l.name.toLowerCase().includes(q))
  }
  return list
})

function isLocSelected(id) {
  return addedLocations.value.some(l => l.id === id)
}

function toggleLocation(loc) {
  const idx = addedLocations.value.findIndex(al => al.id === loc.id)
  if (idx >= 0) {
    addedLocations.value.splice(idx, 1)
  } else {
    addedLocations.value.push(loc)
  }
}

function removeLocation(id) {
  addedLocations.value = addedLocations.value.filter(l => l.id !== id)
}

// ── User prompt ──
const userPrompt = ref('')

// ── Build overrides object ──
function buildOverrides() {
  const excludeVariables = []
  for (const item of props.injectionItems) {
    if (!isEnabled(item)) {
      excludeVariables.push(item.variable)
    }
  }
  return {
    exclude_variables: excludeVariables,
    extra_variables: {},
    added_character_ids: addedCharacters.value.map((c) => c.id),
    added_location_ids: addedLocations.value.map((l) => l.id),
  }
}

// ── Preview ──
const showPreview = ref(false)
const previewLoading = ref(false)
const previewData = ref(null)
let previewTimer = null
let pendingPreviewVersion = 0

async function _fetchPreview() {
  const overrides = buildOverrides()
  const hasOverrides = overrides.exclude_variables.length > 0
    || Object.keys(overrides.extra_variables).length > 0
    || overrides.added_character_ids.length > 0
    || overrides.added_location_ids.length > 0
  const overrideArg = hasOverrides ? overrides : null

  try {
    let data
    if (props.previewFn) {
      data = await props.previewFn(overrideArg)
    } else {
      switch (props.genType) {
        case 'chapter':
          data = (await previewPrompt(props.genId, props.bookId, overrideArg)).data
          break
        case 'arc':
          data = await previewArcPrompt(props.genId, props.bookId, overrideArg)
          break
        case 'volume':
          data = await previewVolumePrompt(props.genId, props.bookId, overrideArg)
          break
        case 'book':
          data = await previewBookPrompt(props.bookId, overrideArg)
          break
        case 'worldview':
          data = await previewWorldviewPrompt(props.bookId, overrideArg)
          break
        case 'map':
          data = await previewMapPrompt(props.bookId, overrideArg)
          break
        case 'character':
          data = await previewCharacterPrompt(props.bookId, overrideArg)
          break
        case 'location':
          data = await previewLocationPrompt(props.bookId, overrideArg)
          break
        default:
          throw new Error(`Unknown gen type: ${props.genType}`)
      }
    }
    previewData.value = data
    previewLoading.value = false
  } catch (e) {
    // Silently ignore stale responses (a newer version is already pending)
    if (pendingPreviewVersion > 0) return
    message.error(e.message || '获取提示词预览失败')
    showPreview.value = false
    previewLoading.value = false
  }
}

function _schedulePreviewRefresh() {
  if (!showPreview.value) return
  pendingPreviewVersion++
  previewLoading.value = true
  if (previewTimer) clearTimeout(previewTimer)
  const myVersion = pendingPreviewVersion
  previewTimer = setTimeout(async () => {
    if (myVersion !== pendingPreviewVersion) return
    await _fetchPreview()
    if (myVersion === pendingPreviewVersion) pendingPreviewVersion = 0
  }, 500)
}

// Auto-refresh preview when configuration changes (while modal is open)
watch([enabledMap, addedCharacters, addedLocations, userPrompt], () => {
  if (showPreview.value) _schedulePreviewRefresh()
}, { deep: true })

async function handlePreview() {
  previewLoading.value = true
  previewData.value = null
  showPreview.value = true
  pendingPreviewVersion++
  await _fetchPreview()
  pendingPreviewVersion = 0
}

// ── Start generation ──
function handleStart() {
  const overrides = buildOverrides()
  emit('start', overrides, userPrompt.value)
}
</script>

<style scoped>
.inj-panel {
  padding: 0;
}

.inj-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px;
}

.inj-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 20px;
}

/* ─── Sections ─── */
.inj-section {
  margin-bottom: 16px;
}

.inj-section-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

/* ─── Injection items ─── */
.inj-items {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.inj-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: 12px;
  cursor: pointer;
  user-select: none;
  transition: border-color 0.15s, background 0.15s;
}

.inj-item:hover {
  border-color: var(--color-accent);
}

.inj-item-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid var(--color-border);
  background: #fff;
  flex-shrink: 0;
}

.inj-item-toggle.active {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}

.inj-item-toggle.muted {
  opacity: 0.4;
}

.inj-item-label {
  color: var(--color-text-primary);
}

.inj-item-hint {
  color: var(--color-text-muted);
  font-size: 11px;
}

/* ─── Collapsible sections ─── */
.inj-section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
  padding: 2px 0;
  margin-bottom: 8px;
}

.inj-section-header:hover .inj-section-label {
  color: var(--color-accent);
}

.inj-section-header .inj-section-label {
  margin-bottom: 0;
}

.inj-section-arrow {
  font-size: 10px;
  color: var(--color-text-muted);
  transition: transform 0.2s;
  flex-shrink: 0;
}

.inj-section-arrow.collapsed {
  transform: rotate(0deg);
}

.inj-section-arrow:not(.collapsed) {
  transform: rotate(90deg);
}

.inj-section-body {
  overflow: hidden;
  transition: max-height 0.2s ease;
}

/* ─── Character filters & grid ─── */
.inj-char-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.inj-char-filter-btn {
  padding: 3px 10px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #fff;
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.inj-char-filter-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.inj-char-filter-btn.active {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}

.inj-char-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  box-sizing: border-box;
  background: #fff;
  margin-bottom: 8px;
}

.inj-char-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px rgba(201, 169, 78, 0.12);
}

.inj-char-grid-loading {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.inj-char-empty {
  padding: 12px 0;
}

.inj-char-no-result {
  text-align: center;
  padding: 16px 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

.inj-char-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 6px;
  margin-bottom: 8px;
}

.inj-char-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 6px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  background: #fff;
}

.inj-char-card:hover {
  border-color: var(--color-accent);
}

.inj-char-card.selected {
  border-color: var(--color-accent);
  background: rgba(201, 169, 78, 0.06);
}

.inj-char-card-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
  text-align: center;
  line-height: 1.3;
  word-break: break-all;
}

.inj-char-card-type {
  font-size: 10px;
  color: var(--color-text-muted);
  padding: 1px 6px;
  border-radius: 8px;
  background: var(--color-bg-page);
}

.inj-char-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.inj-char-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-page);
  font-size: 12px;
  color: var(--color-text-primary);
}

.inj-char-tag-type {
  color: var(--color-text-muted);
  font-size: 11px;
}

.inj-char-tag-remove {
  border: none;
  background: none;
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: 11px;
  padding: 0 2px;
  line-height: 1;
}

.inj-char-tag-remove:hover {
  color: #e74c3c;
}

/* ─── User prompt ─── */
.inj-prompt-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
  background: #fff;
  font-family: inherit;
}

.inj-prompt-textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px rgba(201, 169, 78, 0.12);
}

/* ─── Preview & Actions ─── */
.inj-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.inj-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.inj-btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
  border: 1px solid var(--color-border);
}

.inj-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.inj-btn-ghost {
  background: none;
  border-color: transparent;
  color: var(--color-text-secondary);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.inj-btn-ghost:hover:not(:disabled) {
  color: var(--color-accent);
}

.inj-btn-cancel {
  background: #fff;
  color: var(--color-text-secondary);
}

.inj-btn-cancel:hover {
  border-color: var(--color-text-muted);
  color: var(--color-text-primary);
}

.inj-btn-start {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}

.inj-btn-start:hover:not(:disabled) {
  background: var(--color-accent-light);
  border-color: var(--color-accent-light);
}

.inj-preview-textarea :deep(textarea) {
  font-family: var(--font-mono, 'SF Mono', 'Fira Code', monospace);
  font-size: 13px;
  line-height: 1.7;
}
</style>
