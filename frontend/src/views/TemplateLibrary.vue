<template>
  <div class="template-library">
    <!-- Header -->
    <div class="page-header">
      <h2 class="page-title">提示词模板库</h2>
      <n-button type="primary" @click="showCreateDialog = true">
        <template #icon><n-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M12 5v14M5 12h14"/></svg></n-icon></template>
        新建模板
      </n-button>
    </div>

    <div class="editor-layout">
      <!-- Left: Template list -->
      <div class="template-list-panel">
        <n-input
          v-model:value="searchQuery"
          placeholder="搜索模板..."
          clearable
          size="small"
          class="search-input"
        />
        <n-thing
          v-for="group in filteredGroups"
          :key="group.taskType"
          class="template-group"
        >
          <template #header>
            <n-tag size="small" :bordered="false" class="group-tag">{{ group.taskType || '未分类' }}</n-tag>
          </template>
          <template #description>
            <div
              v-for="tmpl in group.templates"
              :key="tmpl.file_name"
              class="template-item"
              :class="{ active: selectedFile === tmpl.file_name }"
              @click="selectTemplate(tmpl.file_name)"
            >
              <div class="template-item-info">
                <span class="template-item-name">{{ tmpl.name || tmpl.file_name }}</span>
                <span class="template-item-version" v-if="tmpl.version">v{{ tmpl.version }}</span>
              </div>
              <n-tag v-if="tmpl.is_default" size="tiny" type="info" :bordered="false">默认</n-tag>
            </div>
          </template>
        </n-thing>
        <n-empty v-if="filteredGroups.length === 0" description="暂无模板" class="empty-list" />
      </div>

      <!-- Right: Editor -->
      <div class="editor-panel" v-if="currentTemplate">
        <div class="editor-scroll">
          <!-- Frontmatter -->
          <n-collapse :default-expanded-names="['frontmatter', 'body']">
            <n-collapse-item title="元数据" name="frontmatter">
              <n-form label-placement="top" label-width="80" size="small">
                <n-form-item label="模板名称">
                  <n-input v-model:value="editName" placeholder="模板显示名称" />
                </n-form-item>
                <n-space vertical>
                  <n-space>
                    <n-form-item label="任务类型">
                      <n-select
                        v-model:value="editTaskType"
                        :options="taskTypeOptions"
                        placeholder="选择任务类型"
                        style="width: 200px"
                        clearable
                        tag
                      />
                    </n-form-item>
                    <n-form-item label="版本">
                      <n-input v-model:value="editVersion" placeholder="如 1.0" style="width: 120px" />
                    </n-form-item>
                  </n-space>
                </n-space>
                <n-form-item label="描述">
                  <n-input v-model:value="editDescription" placeholder="模板功能描述" type="textarea" :rows="2" />
                </n-form-item>
                <n-form-item label="必需变量">
                  <n-dynamic-tags
                    v-model:value="editRequiredVars"
                    placeholder="输入变量名后回车"
                    :max="10"
                  />
                </n-form-item>
                <n-form-item label="可选变量">
                  <n-dynamic-tags
                    v-model:value="editOptionalVars"
                    placeholder="输入变量名后回车"
                    :max="10"
                  />
                </n-form-item>
                <n-checkbox v-model:checked="editIsDefault" :disabled="currentTemplate.is_default">
                  设为默认模板
                </n-checkbox>
              </n-form>
            </n-collapse-item>

            <n-collapse-item title="正文模板" name="body">
              <div class="editor-wrapper">
                <div class="editor-toolbar">
                  <n-space>
                    <n-button size="tiny" @click="insertVariable('chapter_title')" :secondary="true">章节标题</n-button>
                    <n-button size="tiny" @click="insertVariable('chapter_summary')" :secondary="true">章节摘要</n-button>
                    <n-button size="tiny" @click="insertVariable('writing_style')" :secondary="true">写作风格</n-button>
                    <n-button size="tiny" @click="insertVariable('worldview')" :secondary="true">世界观</n-button>
                    <n-button size="tiny" @click="insertVariable('character_profiles')" :secondary="true">人物设定</n-button>
                    <n-button size="tiny" @click="insertVariable('map_data')" :secondary="true">地图设定</n-button>
                  </n-space>
                </div>
                <div class="textarea-wrapper" ref="editorWrapperRef">
                  <n-input
                    ref="bodyEditorRef"
                    v-model:value="editBody"
                    type="textarea"
                    placeholder="编写提示词模板，使用 {{变量名}} 作为占位符..."
                    :rows="20"
                    @input="onBodyInput"
                    @keyup="onBodyKeyup"
                    @blur="autocompleteOpen = false"
                  />
                  <!-- Variable autocomplete dropdown -->
                  <div
                    v-if="autocompleteOpen && filteredAutocomplete.length > 0"
                    class="autocomplete-dropdown"
                    :style="autocompleteStyle"
                  >
                    <div
                      v-for="(v, i) in filteredAutocomplete"
                      :key="v"
                      class="autocomplete-item"
                      :class="{ active: autocompleteIndex === i }"
                      @mousedown.prevent="applyAutocomplete(v)"
                      @mouseenter="autocompleteIndex = i"
                    >
                      <code>{<!-- -->{<span class="var-highlight">{{ v }}</span>}}</code>
                    </div>
                  </div>
                </div>
              </div>
              <div class="editor-footer">
                <n-space align="center">
                  <n-statistic label="估算 Token" :value="bodyTokenEstimate" :precision="0" />
                  <n-tag v-if="currentTemplate.is_default" type="info" size="small">默认模板 - 不可删除</n-tag>
                </n-space>
              </div>
            </n-collapse-item>
          </n-collapse>
        </div>

        <!-- Action buttons -->
        <div class="editor-actions">
          <n-space>
            <n-button @click="saveTemplate" type="primary" :loading="saving" :disabled="!hasChanges">
              保存
            </n-button>
            <n-button @click="openPreview">
              预览
            </n-button>
            <n-button
              v-if="!currentTemplate.is_default"
              @click="onDraftAsNew"
              :secondary="true"
            >
              另存为新模板
            </n-button>
          </n-space>
          <n-popconfirm v-if="!currentTemplate.is_default" @positive-click="deleteCurrentTemplate">
            <template #trigger>
              <n-button type="error" secondary>删除</n-button>
            </template>
            确定删除模板「{{ currentTemplate.name || currentTemplate.file_name }}」吗？
          </n-popconfirm>
        </div>
      </div>

      <!-- Empty state -->
      <div class="editor-panel editor-empty" v-else>
        <n-empty description="选择一个模板开始编辑">
          <template #extra>
            <n-button size="small" @click="showCreateDialog = true">新建模板</n-button>
          </template>
        </n-empty>
      </div>
    </div>

    <!-- Create dialog -->
    <n-modal v-model:show="showCreateDialog" preset="card" title="新建模板" style="max-width: 500px" :mask-closable="false">
      <n-form label-placement="top" size="small">
        <n-form-item label="文件名">
          <n-input v-model:value="createFileName" placeholder="my_template.md" />
        </n-form-item>
        <n-form-item label="模板名称">
          <n-input v-model:value="createName" placeholder="My Template" />
        </n-form-item>
        <n-form-item label="任务类型">
          <n-select
            v-model:value="createTaskType"
            :options="taskTypeOptions"
            placeholder="选择任务类型"
            clearable
            tag
          />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="createDescription" placeholder="模板描述" type="textarea" :rows="2" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateDialog = false">取消</n-button>
          <n-button type="primary" @click="createTemplate" :disabled="!createFileName.trim()">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Duplicate dialog -->
    <n-modal v-model:show="showDuplicateDialog" preset="card" title="另存为新模板" style="max-width: 500px" :mask-closable="false">
      <n-form label-placement="top" size="small">
        <n-form-item label="新文件名">
          <n-input v-model:value="duplicateFileName" placeholder="new_template.md" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showDuplicateDialog = false">取消</n-button>
          <n-button type="primary" @click="duplicateTemplate" :disabled="!duplicateFileName.trim()">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Preview dialog -->
    <n-modal v-model:show="showPreview" preset="card" title="模板预览" style="max-width: 700px" :mask-closable="false">
      <n-form label-placement="top" size="small">
        <n-form-item
          v-for="v in previewVariables"
          :key="v.name"
          :label="v.name"
        >
          <n-input
            v-model:value="v.value"
            :placeholder="`输入 ${v.name} 的测试值...`"
            type="textarea"
            :rows="2"
          />
        </n-form-item>
      </n-form>
      <n-button @click="renderPreview" :loading="previewLoading" style="margin-bottom: 12px">
        渲染预览
      </n-button>
      <n-divider />
      <n-statistic label="估算 Token" :value="previewTokenEstimate" :precision="0" style="margin-bottom: 8px" />
      <n-input
        v-model:value="previewResult"
        type="textarea"
        :rows="15"
        readonly
        placeholder="点击「渲染预览」查看生成的提示词..."
      />
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import {
  listTemplates,
  getTemplate,
  createTemplate as apiCreateTemplate,
  updateTemplate as apiUpdateTemplate,
  deleteTemplate as apiDeleteTemplate,
  buildPreview as apiBuildPreview,
} from '../api/templates.js'

const message = useMessage()

// ---- state ----
const templates = ref([])
const selectedFile = ref('')
const currentTemplate = ref(null)
const saving = ref(false)
const searchQuery = ref('')

// Edit state
const editName = ref('')
const editTaskType = ref('')
const editVersion = ref('')
const editDescription = ref('')
const editRequiredVars = ref([])
const editOptionalVars = ref([])
const editIsDefault = ref(false)
const editBody = ref('')

// Original snapshot for change detection
const originalSnapshot = ref(null)

const hasChanges = computed(() => {
  if (!currentTemplate.value) return false
  const snap = originalSnapshot.value
  if (!snap) return false
  return (
    editName.value !== snap.name ||
    editTaskType.value !== snap.task_type ||
    editVersion.value !== snap.version ||
    editDescription.value !== snap.description ||
    editIsDefault.value !== snap.is_default ||
    JSON.stringify([...editRequiredVars.value].sort()) !== JSON.stringify([...(snap.required_variables || [])].sort()) ||
    JSON.stringify([...editOptionalVars.value].sort()) !== JSON.stringify([...(snap.optional_variables || [])].sort()) ||
    editBody.value !== snap.body
  )
})

// Autocomplete
const bodyEditorRef = ref(null)
const editorWrapperRef = ref(null)
const autocompleteOpen = ref(false)
const autocompleteIndex = ref(0)
const allVariables = computed(() => {
  const vars = new Set([
    'chapter_title',
    'chapter_summary',
    'writing_style',
    'worldview',
    'character_profiles',
    'chapter_outline',
    'previous_chapter_summary',
    'book_name',
    'book_description',
    'book_outline',
    'volume_title',
    'volume_description',
    'volume_outline',
    'arc_title',
    'arc_description',
    'arc_outlines',
    'volume_outlines',
    'chapter_summaries',
    'current_worldview',
    'map_data',
    ...editRequiredVars.value,
    ...editOptionalVars.value,
  ])
  return [...vars].sort()
})
const autocompleteQuery = ref('')
const filteredAutocomplete = computed(() => {
  if (!autocompleteQuery.value) return allVariables.value
  const q = autocompleteQuery.value.toLowerCase()
  return allVariables.value.filter(v => v.toLowerCase().includes(q))
})
const autocompleteStyle = ref({})

// Create dialog
const showCreateDialog = ref(false)
const createFileName = ref('')
const createName = ref('')
const createTaskType = ref('')
const createDescription = ref('')

// Duplicate dialog
const showDuplicateDialog = ref(false)
const duplicateFileName = ref('')

// Preview dialog
const showPreview = ref(false)
const previewVariables = ref([])
const previewResult = ref('')
const previewTokenEstimate = ref(0)
const previewLoading = ref(false)

// Task type options
const taskTypeOptions = computed(() => {
  const types = new Set(templates.value.map(t => t.task_type).filter(Boolean))
  return [...types].map(t => ({ label: t, value: t }))
})

// Group templates by task_type
const templateGroups = computed(() => {
  const groups = {}
  for (const tmpl of templates.value) {
    const key = tmpl.task_type || '__uncategorized__'
    if (!groups[key]) groups[key] = { taskType: tmpl.task_type, templates: [] }
    groups[key].templates.push(tmpl)
  }
  return Object.values(groups)
})

const filteredGroups = computed(() => {
  if (!searchQuery.value) return templateGroups.value
  const q = searchQuery.value.toLowerCase()
  return templateGroups.value
    .map(g => ({
      ...g,
      templates: g.templates.filter(t =>
        (t.name || '').toLowerCase().includes(q) ||
        (t.file_name || '').toLowerCase().includes(q) ||
        (t.task_type || '').toLowerCase().includes(q)
      ),
    }))
    .filter(g => g.templates.length > 0)
})

const bodyTokenEstimate = computed(() => {
  return Math.max(1, Math.round(editBody.value.length / 3.5))
})

// ---- methods ----

async function loadTemplates() {
  try {
    const res = await listTemplates()
    templates.value = res.data || []
  } catch (e) {
    message.error('加载模板列表失败')
  }
}

async function selectTemplate(fileName) {
  selectedFile.value = fileName
  try {
    const res = await getTemplate(fileName)
    const data = res.data
    currentTemplate.value = {
      file_name: data.file_name,
      name: data.frontmatter?.name || '',
      task_type: data.frontmatter?.task_type || '',
      version: data.frontmatter?.version ? String(data.frontmatter.version) : '',
      description: data.frontmatter?.description || '',
      is_default: data.frontmatter?.is_default || false,
      required_variables: data.frontmatter?.required_variables || [],
      optional_variables: data.frontmatter?.optional_variables || [],
      body: data.body || '',
      token_estimate: data.token_estimate,
    }
    syncEditState()
  } catch (e) {
    message.error('加载模板失败')
    currentTemplate.value = null
  }
}

function syncEditState() {
  if (!currentTemplate.value) return
  editName.value = currentTemplate.value.name
  editTaskType.value = currentTemplate.value.task_type
  editVersion.value = currentTemplate.value.version
  editDescription.value = currentTemplate.value.description
  editRequiredVars.value = [...(currentTemplate.value.required_variables || [])]
  editOptionalVars.value = [...(currentTemplate.value.optional_variables || [])]
  editIsDefault.value = currentTemplate.value.is_default
  editBody.value = currentTemplate.value.body
  originalSnapshot.value = {
    name: editName.value,
    task_type: editTaskType.value,
    version: editVersion.value,
    description: editDescription.value,
    is_default: editIsDefault.value,
    required_variables: [...editRequiredVars.value],
    optional_variables: [...editOptionalVars.value],
    body: editBody.value,
  }
}

async function saveTemplate() {
  if (!currentTemplate.value) return
  saving.value = true
  try {
    const frontmatter = {
      name: editName.value || undefined,
      task_type: editTaskType.value || undefined,
      version: editVersion.value || undefined,
      description: editDescription.value || undefined,
      is_default: editIsDefault.value || undefined,
      required_variables: editRequiredVars.value.length > 0 ? editRequiredVars.value : undefined,
      optional_variables: editOptionalVars.value.length > 0 ? editOptionalVars.value : undefined,
    }
    // Remove undefined keys
    Object.keys(frontmatter).forEach(k => frontmatter[k] === undefined && delete frontmatter[k])

    await apiUpdateTemplate(currentTemplate.value.file_name, {
      frontmatter,
      body: editBody.value,
    })
    message.success('模板已保存')
    // Refresh
    if (currentTemplate.value.file_name !== selectedFile.value) {
      await selectTemplate(selectedFile.value)
    } else {
      await selectTemplate(currentTemplate.value.file_name)
    }
    await loadTemplates()
  } catch (e) {
    message.error('保存失败：' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function deleteCurrentTemplate() {
  if (!currentTemplate.value) return
  try {
    await apiDeleteTemplate(currentTemplate.value.file_name)
    message.success('模板已删除')
    currentTemplate.value = null
    selectedFile.value = ''
    await loadTemplates()
  } catch (e) {
    message.error('删除失败：' + (e.response?.data?.detail || e.message))
  }
}

async function createTemplate() {
  let fileName = createFileName.value.trim()
  if (!fileName.endsWith('.md')) fileName += '.md'
  const frontmatter = {}
  if (createName.value) frontmatter.name = createName.value
  if (createTaskType.value) frontmatter.task_type = createTaskType.value
  if (createDescription.value) frontmatter.description = createDescription.value
  frontmatter.version = '1.0'
  try {
    await apiCreateTemplate({
      file_name: fileName,
      frontmatter,
      body: '',
    })
    message.success('模板已创建')
    showCreateDialog.value = false
    createFileName.value = ''
    createName.value = ''
    createTaskType.value = ''
    createDescription.value = ''
    await loadTemplates()
    await selectTemplate(fileName)
  } catch (e) {
    message.error('创建失败：' + (e.response?.data?.detail || e.message))
  }
}

function onDraftAsNew() {
  duplicateFileName.value = ''
  showDuplicateDialog.value = true
}

async function duplicateTemplate() {
  let fileName = duplicateFileName.value.trim()
  if (!fileName.endsWith('.md')) fileName += '.md'
  const frontmatter = {
    name: editName.value ? (editName.value + ' (副本)') : undefined,
    task_type: editTaskType.value || undefined,
    version: '1.0',
    description: editDescription.value || undefined,
    required_variables: editRequiredVars.value.length > 0 ? editRequiredVars.value : undefined,
    optional_variables: editOptionalVars.value.length > 0 ? editOptionalVars.value : undefined,
  }
  Object.keys(frontmatter).forEach(k => frontmatter[k] === undefined && delete frontmatter[k])

  try {
    await apiCreateTemplate({
      file_name: fileName,
      frontmatter,
      body: editBody.value,
    })
    message.success('已另存为新模板')
    showDuplicateDialog.value = false
    await loadTemplates()
    await selectTemplate(fileName)
  } catch (e) {
    message.error('另存失败：' + (e.response?.data?.detail || e.message))
  }
}

function openPreview() {
  // Build variable list from frontmatter + built-in
  const varNames = new Set([
    ...editRequiredVars.value,
    ...editOptionalVars.value,
    'chapter_title', 'chapter_summary', 'writing_style', 'worldview',
    'character_profiles', 'chapter_outline', 'previous_chapter_summary', 'map_data',
  ])
  previewVariables.value = [...varNames].map(name => ({
    name,
    value: '',
  }))
  previewResult.value = ''
  previewTokenEstimate.value = 0
  showPreview.value = true
}

async function renderPreview() {
  previewLoading.value = true
  try {
    const vars = {}
    for (const v of previewVariables.value) {
      if (v.value) vars[v.name] = v.value
    }
    const res = await apiBuildPreview(currentTemplate.value.file_name, vars)
    previewResult.value = res.data.prompt
    previewTokenEstimate.value = res.data.token_estimate
  } catch (e) {
    message.error('预览渲染失败：' + (e.response?.data?.detail || e.message))
  } finally {
    previewLoading.value = false
  }
}

// Body editor autocomplete
function onBodyInput(val) {
  const el = bodyEditorRef.value
  if (!el || !el.textareaEl) return
  const ta = el.textareaEl
  const cursorPos = ta.selectionStart
  const textBefore = editBody.value.substring(0, cursorPos)
  const match = textBefore.match(/\{\{(\w*)$/)
  if (match) {
    autocompleteQuery.value = match[1]
    autocompleteOpen.value = true
    autocompleteIndex.value = 0
    // Position the dropdown
    nextTick(() => {
      const rect = ta.getBoundingClientRect()
      // Approximate cursor position based on text length and rows
      const lines = textBefore.split('\n')
      const lineHeight = 20
      const charWidth = 8
      const lineNum = lines.length - 1
      const colNum = lines[lineNum].length
      autocompleteStyle.value = {
        top: `${Math.min(lineNum * lineHeight + 24, 300)}px`,
        left: `${Math.min(colNum * charWidth, rect.width - 200)}px`,
      }
    })
  } else {
    autocompleteOpen.value = false
  }
}

function onBodyKeyup(e) {
  if (autocompleteOpen.value) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      autocompleteIndex.value = Math.min(autocompleteIndex.value + 1, filteredAutocomplete.value.length - 1)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      autocompleteIndex.value = Math.max(autocompleteIndex.value - 1, 0)
    } else if (e.key === 'Enter' || e.key === 'Tab') {
      if (filteredAutocomplete.value.length > 0) {
        e.preventDefault()
        applyAutocomplete(filteredAutocomplete.value[autocompleteIndex.value])
      }
    } else if (e.key === 'Escape') {
      autocompleteOpen.value = false
    }
  }
}

function applyAutocomplete(varName) {
  const el = bodyEditorRef.value
  if (!el || !el.textareaEl) return
  const ta = el.textareaEl
  const cursorPos = ta.selectionStart
  const textBefore = editBody.value.substring(0, cursorPos)
  const textAfter = editBody.value.substring(cursorPos)
  // Replace the last {{ partial with {{varName}}
  const match = textBefore.match(/\{\{(\w*)$/)
  if (!match) return
  const beforeMatch = textBefore.substring(0, textBefore.lastIndexOf('{{'))
  editBody.value = beforeMatch + '{{' + varName + '}}' + textAfter
  autocompleteOpen.value = false
  nextTick(() => {
    const newPos = beforeMatch.length + varName.length + 4
    ta.setSelectionRange(newPos, newPos)
    ta.focus()
  })
}

function insertVariable(name) {
  const el = bodyEditorRef.value
  if (!el || !el.textareaEl) return
  const ta = el.textareaEl
  const cursorPos = ta.selectionStart
  const textBefore = editBody.value.substring(0, cursorPos)
  const textAfter = editBody.value.substring(cursorPos)
  editBody.value = textBefore + '{{' + name + '}}' + textAfter
  nextTick(() => {
    const newPos = textBefore.length + name.length + 4
    ta.setSelectionRange(newPos, newPos)
    ta.focus()
  })
}

// ---- lifecycle ----
onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.template-library {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
}

.editor-layout {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
}

/* Left panel */
.template-list-panel {
  width: 280px;
  flex-shrink: 0;
  overflow-y: auto;
  background: var(--color-bg-2, #fff);
  border-radius: 8px;
  border: 1px solid var(--color-border, #e0e0e0);
  padding: 12px;
}

.search-input {
  margin-bottom: 12px;
}

.template-group {
  margin-bottom: 8px;
}

.group-tag {
  margin-bottom: 4px;
}

.template-item {
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  transition: background 0.15s;
}

.template-item:hover {
  background: var(--color-hover, #f5f5f5);
}

.template-item.active {
  background: var(--color-primary-opacity, #ecf5ff);
}

.template-item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.template-item-name {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.template-item-version {
  font-size: 11px;
  color: var(--color-text-3, #999);
}

.empty-list {
  padding: 40px 0;
}

/* Right panel */
.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-2, #fff);
  border-radius: 8px;
  border: 1px solid var(--color-border, #e0e0e0);
  min-height: 0;
}

.editor-empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.editor-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.editor-wrapper {
  position: relative;
}

.editor-toolbar {
  margin-bottom: 8px;
}

.textarea-wrapper {
  position: relative;
}

.editor-footer {
  margin-top: 8px;
}

.editor-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid var(--color-border, #e0e0e0);
  background: var(--color-bg-1, #fafafa);
  border-radius: 0 0 8px 8px;
}

/* Autocomplete dropdown */
.autocomplete-dropdown {
  position: absolute;
  z-index: 100;
  background: #fff;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  max-height: 200px;
  overflow-y: auto;
  min-width: 180px;
}

.autocomplete-item {
  padding: 6px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #333;
  transition: background 0.1s;
}

.autocomplete-item:hover,
.autocomplete-item.active {
  background: var(--color-primary-opacity, #ecf5ff);
}

.autocomplete-item code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 12px;
  background: none;
  padding: 0;
}

.var-highlight {
  color: var(--color-primary, #2080f0);
  font-weight: 600;
}
</style>
