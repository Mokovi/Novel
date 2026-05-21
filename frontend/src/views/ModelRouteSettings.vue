<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">设置</h1>
      <p class="page-desc">管理模型 API、方案、功能绑定和生成参数。</p>
    </div>

    <n-tabs v-model:value="activeTab" type="line">
      <!-- Tab 1: Model APIs -->
      <n-tab-pane name="apis" tab="模型 API">
        <div class="tab-content">
          <SectionHeader title="模型 API">
            <n-button type="primary" @click="openApiCreate" class="add-btn">添加 API</n-button>
          </SectionHeader>
          <div class="card-list">
            <div
              v-for="(api, i) in apis"
              :key="api.id"
              class="enhanced-card"
              :class="[api.enabled ? 'card-accent-success' : 'card-accent-muted', { 'card-disabled': !api.enabled }]"
              :style="{ animationDelay: i * 0.05 + 's' }"
            >
              <div class="card-header">
                <div class="card-header-left">
                  <n-text class="card-title">{{ api.name }}</n-text>
                  <n-tag :type="api.enabled ? 'success' : 'default'" size="small">
                    {{ api.enabled ? '启用' : '禁用' }}
                  </n-tag>
                </div>
              </div>
              <div class="api-descs">
                <div class="api-desc-item">
                  <span class="api-desc-label">提供商</span>
                  <span class="api-desc-value">{{ api.provider }}</span>
                </div>
                <div class="api-desc-item">
                  <span class="api-desc-label">模型</span>
                  <span class="api-desc-value">{{ api.model_name }}</span>
                </div>
                <div class="api-desc-item">
                  <span class="api-desc-label">API Key</span>
                  <span class="api-desc-value">{{ api.api_key_masked || '-' }}</span>
                </div>
                <div class="api-desc-item">
                  <span class="api-desc-label">Base URL</span>
                  <span class="api-desc-value">{{ api.api_base_url || '(默认)' }}</span>
                </div>
              </div>
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
          <SectionHeader title="方案管理">
            <n-button type="primary" @click="openPlanCreate" class="add-btn">添加方案</n-button>
          </SectionHeader>
          <div class="card-list">
            <div v-for="(plan, i) in plans" :key="plan.id" class="enhanced-card card-accent-gold" :style="{ animationDelay: i * 0.05 + 's' }">
              <div class="card-header">
                <n-text class="card-title">{{ plan.name }}</n-text>
              </div>
              <p v-if="plan.description" class="plan-desc">{{ plan.description }}</p>
              <div class="plan-apis">
                <div
                  v-for="(api, idx) in plan.apis"
                  :key="api.id"
                  class="plan-api-item"
                >
                  <span class="plan-api-index">{{ idx + 1 }}</span>
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
          <SectionHeader title="功能绑定" />
          <div class="card-list">
            <div v-for="(key, i) of taskKeys" :key="key" class="enhanced-card card-accent-info" :style="{ animationDelay: i * 0.05 + 's' }">
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
                  <template v-for="(api, idx) in (plans.find(p => p.id === getBindingPlanId(key))?.apis || [])" :key="api.id">
                    <span class="binding-api-arrow" v-if="idx > 0" />
                    <n-tag
                      size="small"
                      :type="api.enabled ? 'success' : 'default'"
                      class="binding-api-tag"
                    >
                      {{ api.name }} ({{ api.model_name }})
                    </n-tag>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </n-tab-pane>

      <!-- Tab 4: Generation Settings -->
      <n-tab-pane name="generation" tab="生成设置">
        <div class="tab-content">
          <SectionHeader title="生成参数" />
          <div class="enhanced-card card-accent-gold gen-settings-card">
            <div class="gen-setting-item">
              <div class="gen-setting-number">1</div>
              <div class="gen-setting-content">
                <label class="gen-setting-label">注入前文章节摘要数量</label>
                <p class="gen-setting-hint">下一章生成时，会在提示词中注入前 N 章的 AI 摘要作为上下文参考。</p>
                <n-input-number
                  v-model:value="settingsStore.previousChapterCount"
                  :min="0"
                  :max="10"
                  :step="1"
                  style="width: 200px"
                />
              </div>
            </div>
            <div class="gen-setting-divider" />
            <div class="gen-setting-item">
              <div class="gen-setting-number">2</div>
              <div class="gen-setting-content">
                <label class="gen-setting-label">大纲生成轮数</label>
                <p class="gen-setting-hint">生成大纲时运行的推理轮数（1-5），轮数越多大纲越精细。</p>
                <n-input-number
                  v-model:value="settingsStore.outlineGenerationCount"
                  :min="1"
                  :max="5"
                  :step="1"
                  style="width: 200px"
                />
              </div>
            </div>
            <div class="gen-setting-divider" />
            <div class="gen-setting-item">
              <div class="gen-setting-number">3</div>
              <div class="gen-setting-content">
                <label class="gen-setting-label">上层大纲注入层级</label>
                <p class="gen-setting-hint">生成低层级纲要时，自动注入上层纲要内容。0=不注入，1=注入上一层（生成事件纲注入卷纲，生成章节注入事件纲）。</p>
                <n-input-number
                  v-model:value="settingsStore.outlineInjectionDepth"
                  :min="0"
                  :max="3"
                  :step="1"
                  style="width: 200px"
                />
              </div>
            </div>
            <div class="gen-setting-footer">
              <n-button
                type="primary"
                :loading="settingsStore.loading"
                @click="handleSaveGenSettings"
              >
                保存设置
              </n-button>
            </div>
          </div>
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
import SectionHeader from '../components/common/SectionHeader.vue'

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

.page-header {
  margin-bottom: 28px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 6px;
  position: relative;
}
.page-title::after {
  content: '';
  display: block;
  width: 40px;
  height: 3px;
  border-radius: 2px;
  background: var(--color-accent);
  margin-top: 6px;
}

.page-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 8px 0 0;
}

.tab-content {
  animation: fade-in 0.3s ease;
}

/* ── Enhanced Cards ── */
.enhanced-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-card-rest);
  transition: var(--transition-card);
  animation: fade-in-up 0.35s ease both;
}
.enhanced-card:hover {
  box-shadow: var(--shadow-card-lift);
  transform: translateY(-2px);
}

.card-accent-gold { border-left: 3px solid var(--color-accent); }
.card-accent-success { border-left: 3px solid var(--color-success); }
.card-accent-info { border-left: 3px solid var(--color-info); }
.card-accent-muted { border-left: 3px solid var(--color-text-muted); }

.card-disabled {
  opacity: 0.75;
}

/* ── Card list ── */
.card-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

/* ── API descriptions grid ── */
.api-descs {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}
@media (min-width: 640px) {
  .api-descs {
    grid-template-columns: 1fr 1fr;
  }
}
.api-desc-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 12px;
  background: var(--color-bg-page);
  border-radius: 6px;
}
.api-desc-label {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.api-desc-value {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
}

/* ── Plan card ── */
.plan-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 4px 0 16px;
}

.plan-apis {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 0;
}

.plan-api-item {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
  border-radius: 6px;
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

/* ── Binding card ── */
.binding-select {
  margin-top: 4px;
}

.binding-select :deep(.n-form-item-label) {
  font-size: 13px;
}

.binding-apis {
  margin-top: 12px;
}

.binding-apis-label {
  font-size: 12px;
  display: block;
  margin-bottom: 8px;
}

.binding-api-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0;
}

.binding-api-tag {
  margin: 2px 0;
}

.binding-api-arrow {
  display: inline-flex;
  align-items: center;
  margin: 0 8px;
  color: var(--color-text-muted);
}
.binding-api-arrow::after {
  content: '→';
  font-size: 14px;
}

/* ── Generation settings card ── */
.gen-settings-card {
  max-width: 600px;
}

.gen-setting-item {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.gen-setting-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.gen-setting-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.gen-setting-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.gen-setting-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.gen-setting-divider {
  height: 1px;
  background: var(--color-border);
  margin: 20px 0;
  margin-left: 44px;
}

.gen-setting-footer {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
}

/* ── Shared ── */
.btn-danger-text {
  color: var(--color-error) !important;
}

.empty-state {
  margin-top: 40px;
}
</style>
