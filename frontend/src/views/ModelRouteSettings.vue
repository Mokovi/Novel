<template>
  <div class="settings-page">
    <h1 class="page-title">设置</h1>
    <p class="page-desc">管理模型 API、方案、功能绑定和生成参数。</p>

    <n-tabs v-model:value="activeTab" type="line">
      <!-- Tab 1: Model APIs -->
      <n-tab-pane name="apis" tab="模型 API">
        <div class="tab-content">
          <n-button type="primary" @click="openApiCreate" class="add-btn">添加 API</n-button>
          <div class="card-list">
            <div
              v-for="api in apis"
              :key="api.id"
              class="api-card"
              :class="{ disabled: !api.enabled }"
            >
              <div class="card-header">
                <div class="card-header-left">
                  <n-text class="card-title">{{ api.name }}</n-text>
                  <n-tag :type="api.enabled ? 'success' : 'default'" size="small">
                    {{ api.enabled ? '启用' : '禁用' }}
                  </n-tag>
                </div>
              </div>
              <n-descriptions :column="2" size="small" bordered class="card-descriptions">
                <n-descriptions-item label="提供商">{{ api.provider }}</n-descriptions-item>
                <n-descriptions-item label="模型">{{ api.model_name }}</n-descriptions-item>
                <n-descriptions-item label="API Key">{{ api.api_key_masked || '-' }}</n-descriptions-item>
                <n-descriptions-item label="Base URL">{{ api.api_base_url || '(默认)' }}</n-descriptions-item>
              </n-descriptions>
              <div class="card-actions">
                <n-button size="small" @click="openApiEdit(api)">编辑</n-button>
                <n-button size="small" :loading="apiTesting === api.id" @click="testApiConnection(api.id)">测试</n-button>
                <n-tag v-if="testResults[api.id]" :type="testResults[api.id].success ? 'success' : 'error'" size="small">
                  {{ testResults[api.id].success ? '✓ 连接成功' : '✗ ' + testResults[api.id].error }}
                </n-tag>
                <n-popconfirm @positive-click="removeApi(api.id)">
                  <template #trigger>
                    <n-button size="small" class="btn-danger-text">删除</n-button>
                  </template>
                  确认删除此 API？
                </n-popconfirm>
              </div>
            </div>
            <n-empty v-if="!apis.length" description="暂无模型 API，点击添加" class="empty-state" />
          </div>
        </div>
      </n-tab-pane>

      <!-- Tab 2: Plans -->
      <n-tab-pane name="plans" tab="方案管理">
        <div class="tab-content">
          <n-button type="primary" @click="openPlanCreate" class="add-btn">添加方案</n-button>
          <div class="card-list">
            <div v-for="plan in plans" :key="plan.id" class="plan-card">
              <div class="card-header">
                <n-text class="card-title">{{ plan.name }}</n-text>
              </div>
              <p v-if="plan.description" class="plan-desc">{{ plan.description }}</p>
              <div class="plan-apis">
                <div
                  v-for="(api, i) in plan.apis"
                  :key="api.id"
                  class="plan-api-item"
                >
                  <span class="plan-api-index">{{ i + 1 }}</span>
                  <span class="plan-api-name">{{ api.name }} ({{ api.model_name }})</span>
                  <n-tag :type="api.enabled ? 'success' : 'default'" size="small">
                    {{ api.enabled ? '启用' : '禁用' }}
                  </n-tag>
                </div>
                <n-empty v-if="!plan.apis.length" description="方案中没有 API" size="small" />
              </div>
              <div class="card-actions">
                <n-button size="small" @click="openPlanEdit(plan)">编辑</n-button>
                <n-popconfirm @positive-click="removePlan(plan.id)">
                  <template #trigger>
                    <n-button size="small" class="btn-danger-text">删除</n-button>
                  </template>
                  确认删除此方案？
                </n-popconfirm>
              </div>
            </div>
            <n-empty v-if="!plans.length" description="暂无方案，点击添加" class="empty-state" />
          </div>
        </div>
      </n-tab-pane>

      <!-- Tab 3: Bindings -->
      <n-tab-pane name="bindings" tab="功能绑定">
        <div class="tab-content">
          <div class="card-list">
            <div v-for="key of taskKeys" :key="key" class="binding-card">
              <div class="card-header">
                <n-text class="card-title">{{ taskLabels[key] || key }}</n-text>
                <n-tag size="small">{{ key }}</n-tag>
              </div>
              <n-form-item label="使用方案" class="binding-select">
                <n-select
                  :value="getBindingPlanId(key)"
                  :options="planSelectOptions"
                  :loading="bindingSaving === key"
                  @update:value="(v) => onBind(key, v)"
                />
              </n-form-item>
              <div v-if="getBindingPlanId(key)" class="binding-apis">
                <n-text depth="3" class="binding-apis-label">绑定的方案中包含 API：</n-text>
                <div class="binding-api-tags">
                  <n-tag
                    v-for="api in (plans.find(p => p.id === getBindingPlanId(key))?.apis || [])"
                    :key="api.id"
                    size="small"
                    :type="api.enabled ? 'success' : 'default'"
                  >
                    {{ api.name }} ({{ api.model_name }})
                  </n-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </n-tab-pane>

      <!-- Tab 4: Generation Settings -->
      <n-tab-pane name="generation" tab="生成设置">
        <div class="tab-content">
          <n-card title="生成参数" class="settings-card">
            <n-space vertical :size="16">
              <n-form-item label="注入前文章节摘要数量">
                <n-text depth="3" class="form-hint">
                  下一章生成时，会在提示词中注入前 N 章的 AI 摘要作为上下文参考。
                </n-text>
                <n-input-number
                  v-model:value="settingsStore.previousChapterCount"
                  :min="0"
                  :max="10"
                  :step="1"
                  style="width: 200px"
                />
              </n-form-item>
              <n-form-item label="大纲生成轮数">
                <n-text depth="3" class="form-hint">
                  生成大纲时运行的推理轮数（1-5），轮数越多大纲越精细。
                </n-text>
                <n-input-number
                  v-model:value="settingsStore.outlineGenerationCount"
                  :min="1"
                  :max="5"
                  :step="1"
                  style="width: 200px"
                />
              </n-form-item>
              <n-form-item label="上层大纲注入层级">
                <n-text depth="3" class="form-hint">
                  生成低层级纲要时，自动注入上层纲要内容。0=不注入，1=注入上一层（生成事件纲注入卷纲，生成章节注入事件纲）。
                </n-text>
                <n-input-number
                  v-model:value="settingsStore.outlineInjectionDepth"
                  :min="0"
                  :max="3"
                  :step="1"
                  style="width: 200px"
                />
              </n-form-item>

              <n-button
                type="primary"
                :loading="settingsStore.loading"
                @click="handleSaveGenSettings"
              >
                保存设置
              </n-button>
            </n-space>
          </n-card>
        </div>
      </n-tab-pane>
    </n-tabs>

    <!-- API Modal -->
    <n-modal v-model:show="apiModal" :mask-closable="false">
      <n-card style="width: 500px" :title="apiEditing ? '编辑 API' : '添加 API'">
        <n-form>
          <n-form-item label="名称" required>
            <n-input v-model:value="apiForm.name" placeholder="如: DeepSeek V4 Pro" />
          </n-form-item>
          <n-form-item label="提供商" required>
            <n-select v-model:value="apiForm.provider" :options="providerOptions" />
          </n-form-item>
          <n-form-item label="模型名称" required>
            <n-input v-model:value="apiForm.model_name" placeholder="如: deepseek-chat" />
          </n-form-item>
          <n-form-item label="API Key">
            <n-input v-model:value="apiForm.api_key" type="password" show-password-on="click" placeholder="留空保持不变" />
          </n-form-item>
          <n-form-item label="API Base URL">
            <n-input v-model:value="apiForm.api_base_url" placeholder="留空使用默认" />
          </n-form-item>
          <n-form-item label="启用">
            <n-switch v-model:value="apiForm.enabled" />
          </n-form-item>
        </n-form>
        <template #action>
          <n-space justify="end">
            <n-button @click="apiModal = false">取消</n-button>
            <n-button type="primary" :loading="apiSaving" @click="saveApi">保存</n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>

    <!-- Plan Modal -->
    <n-modal v-model:show="planModal" :mask-closable="false">
      <n-card style="width: 500px" :title="planEditing ? '编辑方案' : '添加方案'">
        <n-form>
          <n-form-item label="名称" required>
            <n-input v-model:value="planForm.name" placeholder="如: 主力方案" />
          </n-form-item>
          <n-form-item label="说明">
            <n-input v-model:value="planForm.description" type="textarea" placeholder="可选说明" />
          </n-form-item>
          <n-form-item label="包含的 API (按轮询顺序)">
            <n-transfer
              v-model:value="planForm.api_ids"
              :options="transferOptions"
            />
          </n-form-item>
        </n-form>
        <template #action>
          <n-space justify="end">
            <n-button @click="planModal = false">取消</n-button>
            <n-button type="primary" :loading="planSaving" @click="savePlan">保存</n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useMessage } from 'naive-ui'
import { listModelApis, createModelApi, updateModelApi, deleteModelApi, testModelApi } from '../api/model-apis.js'
import { listPlans, createPlan, updatePlan, deletePlan } from '../api/plans.js'
import { listTaskBindings, updateTaskBinding, deleteTaskBinding } from '../api/task-bindings.js'
import { useSettingsStore } from '../stores/settings.js'

const message = useMessage()
const settingsStore = useSettingsStore()

const activeTab = ref('apis')
const apis = ref([])
const plans = ref([])

const providerOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'Anthropic', value: 'anthropic' },
]

const taskKeys = ['outline_design', 'chapter_writing', 'character_design', 'worldbuilding', 'revision']

const taskLabels = {
  outline_design: '大纲设计',
  chapter_writing: '章节写作',
  character_design: '人物设计',
  worldbuilding: '世界观构建',
  revision: '润色修改',
}

onMounted(async () => {
  const [a, p, b] = await Promise.all([
    listModelApis().catch(() => ({ data: [] })),
    listPlans().catch(() => ({ data: [] })),
    listTaskBindings().catch(() => ({ data: [] })),
    settingsStore.fetchGenerationSettings(),
  ])
  apis.value = a.data
  plans.value = p.data
  bindings.value = b.data
})

async function handleSaveGenSettings() {
  await settingsStore.saveGenerationSettings()
  message.success('设置已保存')
}

const transferOptions = computed(() =>
  apis.value.map(a => ({ label: `${a.name} (${a.model_name})`, value: a.id, disabled: !a.enabled }))
)

const planSelectOptions = computed(() => [
  { label: '(未绑定)', value: null },
  ...plans.value.map(p => ({
    label: `${p.name} (${p.apis.map(a => a.name).join(', ') || '无API'})`,
    value: p.id,
  })),
])

// ═══ Tab 1: Model APIs ═══
const apiModal = ref(false)
const apiEditing = ref(null)
const apiForm = ref({ name: '', provider: 'openai', model_name: '', api_key: '', api_base_url: '', enabled: true, max_tokens: null, temperature: null })
const apiSaving = ref(false)
const apiTesting = ref(null)
const testResults = ref({})

function openApiCreate() {
  apiEditing.value = null
  apiForm.value = { name: '', provider: 'openai', model_name: '', api_key: '', api_base_url: '', enabled: true, max_tokens: null, temperature: null }
  apiModal.value = true
}

function openApiEdit(api) {
  apiEditing.value = api.id
  apiForm.value = { ...api, api_key: '' }
  apiModal.value = true
}

async function saveApi() {
  apiSaving.value = true
  try {
    const data = { ...apiForm.value }
    if (!data.api_key) delete data.api_key
    if (apiEditing.value) {
      await updateModelApi(apiEditing.value, data)
    } else {
      await createModelApi(data)
    }
    apiModal.value = false
    const res = await listModelApis()
    apis.value = res.data
    message.success('保存成功')
  } catch (e) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    apiSaving.value = false
  }
}

async function removeApi(id) {
  try {
    await deleteModelApi(id)
    const res = await listModelApis()
    apis.value = res.data
    message.success('删除成功')
  } catch (e) {
    message.error('删除失败')
  }
}

async function testApiConnection(id) {
  apiTesting.value = id
  delete testResults.value[id]
  try {
    const res = await testModelApi(id)
    testResults.value[id] = { success: res.data.success, error: res.data.error }
    if (res.data.success) {
      message.success(`「${apis.value.find(a => a.id === id)?.name}」连接成功`)
    } else {
      message.error(`连接失败: ${res.data.error}`)
    }
  } catch (e) {
    testResults.value[id] = { success: false, error: e.message }
    message.error(`请求失败: ${e.message}`)
  } finally {
    apiTesting.value = null
  }
}

// ═══ Tab 2: Plans ═══
const planModal = ref(false)
const planEditing = ref(null)
const planForm = ref({ name: '', description: '', api_ids: [] })
const planSaving = ref(false)

function openPlanCreate() {
  planEditing.value = null
  planForm.value = { name: '', description: '', api_ids: [] }
  planModal.value = true
}

function openPlanEdit(plan) {
  planEditing.value = plan.id
  planForm.value = { name: plan.name, description: plan.description || '', api_ids: plan.apis.map(a => a.id) }
  planModal.value = true
}

async function savePlan() {
  planSaving.value = true
  try {
    if (planEditing.value) {
      await updatePlan(planEditing.value, planForm.value)
    } else {
      await createPlan(planForm.value)
    }
    planModal.value = false
    const res = await listPlans()
    plans.value = res.data
    message.success('保存成功')
  } catch (e) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    planSaving.value = false
  }
}

async function removePlan(id) {
  try {
    await deletePlan(id)
    const res = await listPlans()
    plans.value = res.data
    message.success('删除成功')
  } catch (e) {
    message.error('删除失败')
  }
}

// ═══ Tab 3: Bindings ═══
const bindings = ref([])
const bindingSaving = ref(null)

async function onBind(taskKey, planId) {
  bindingSaving.value = taskKey
  try {
    if (planId) {
      await updateTaskBinding(taskKey, { plan_id: planId })
    } else {
      await deleteTaskBinding(taskKey)
    }
    const res = await listTaskBindings()
    bindings.value = res.data
    message.success('绑定成功')
  } catch (e) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally {
    bindingSaving.value = null
  }
}

function getBindingPlanId(taskKey) {
  const b = bindings.value.find(x => x.task_key === taskKey)
  return b?.plan_id || null
}
</script>

<style scoped>
.settings-page {
  max-width: 860px;
  margin: 0 auto;
}

.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 6px;
}

.page-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 24px;
}

.tab-content {
  animation: fade-in 0.3s ease;
}

.add-btn {
  margin-bottom: 16px;
}

/* Card list */
.card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* API Card */
.api-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px;
  border-left: 3px solid var(--color-success);
  animation: fade-in-up 0.35s ease both;
}

.api-card.disabled {
  border-left-color: var(--color-text-muted);
  opacity: 0.75;
}

/* Plan Card */
.plan-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px;
  animation: fade-in-up 0.35s ease both;
}

.plan-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 4px 0 12px;
}

.plan-apis {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.plan-api-item {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  font-size: 13px;
}

.plan-api-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.plan-api-name {
  color: var(--color-text-primary);
}

/* Binding Card */
.binding-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px;
  animation: fade-in-up 0.35s ease both;
}

.binding-select {
  margin-top: 8px;
}

.binding-select :deep(.n-form-item-label) {
  font-size: 13px;
}

.binding-apis {
  margin-top: 8px;
}

.binding-apis-label {
  font-size: 12px;
  display: block;
  margin-bottom: 6px;
}

.binding-api-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* Shared */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.card-descriptions {
  margin-bottom: 12px;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-danger-text {
  color: var(--color-error) !important;
}

.empty-state {
  margin-top: 40px;
}

.settings-card {
  max-width: 500px;
}

.form-hint {
  display: block;
  margin-bottom: 6px;
}
</style>
