<template>
  <n-space vertical :size="16">
    <n-h1>模型路由配置</n-h1>
    <n-p>管理模型 API、方案和功能绑定。</n-p>

    <n-tabs v-model:value="activeTab" type="line">
      <!-- Tab 1: Model APIs -->
      <n-tab-pane name="apis" tab="模型 API">
        <n-space vertical :size="12">
          <n-button type="primary" @click="openApiCreate">添加 API</n-button>
          <n-card v-for="api in apis" :key="api.id" size="small">
            <template #header>
              <n-space align="center" justify="space-between">
                <n-text strong>{{ api.name }}</n-text>
                <n-tag :type="api.enabled ? 'success' : 'default'" size="small">
                  {{ api.enabled ? '启用' : '禁用' }}
                </n-tag>
              </n-space>
            </template>
            <n-descriptions :column="2" size="small" bordered>
              <n-descriptions-item label="提供商">{{ api.provider }}</n-descriptions-item>
              <n-descriptions-item label="模型">{{ api.model_name }}</n-descriptions-item>
              <n-descriptions-item label="API Key">{{ api.api_key_masked || '-' }}</n-descriptions-item>
              <n-descriptions-item label="Base URL">{{ api.api_base_url || '(默认)' }}</n-descriptions-item>
            </n-descriptions>
            <template #action>
              <n-space>
                <n-button size="small" @click="openApiEdit(api)">编辑</n-button>
                <n-button size="small" :loading="apiTesting === api.id" @click="testApiConnection(api.id)">测试</n-button>
                <n-popconfirm @positive-click="removeApi(api.id)">
                  <template #trigger>
                    <n-button size="small" type="error">删除</n-button>
                  </template>
                  确认删除此 API？
                </n-popconfirm>
              </n-space>
            </template>
          </n-card>
          <n-empty v-if="!apis.length" description="暂无模型 API，点击添加" />
        </n-space>
      </n-tab-pane>

      <!-- Tab 2: Plans -->
      <n-tab-pane name="plans" tab="方案管理">
        <n-space vertical :size="12">
          <n-button type="primary" @click="openPlanCreate">添加方案</n-button>
          <n-card v-for="plan in plans" :key="plan.id" size="small">
            <template #header>
              <n-text strong>{{ plan.name }}</n-text>
            </template>
            <n-p v-if="plan.description" depth="3">{{ plan.description }}</n-p>
            <n-tag v-for="(api, i) in plan.apis" :key="api.id" style="margin: 2px">
              {{ i + 1 }}. {{ api.name }} ({{ api.model_name }})
              <n-tag :type="api.enabled ? 'success' : 'default'" size="small" style="margin-left: 4px">
                {{ api.enabled ? '启用' : '禁用' }}
              </n-tag>
            </n-tag>
            <n-empty v-if="!plan.apis.length" description="方案中没有 API" size="small" />
            <template #action>
              <n-space>
                <n-button size="small" @click="openPlanEdit(plan)">编辑</n-button>
                <n-popconfirm @positive-click="removePlan(plan.id)">
                  <template #trigger>
                    <n-button size="small" type="error">删除</n-button>
                  </template>
                  确认删除此方案？
                </n-popconfirm>
              </n-space>
            </template>
          </n-card>
          <n-empty v-if="!plans.length" description="暂无方案，点击添加" />
        </n-space>
      </n-tab-pane>

      <!-- Tab 3: Bindings -->
      <n-tab-pane name="bindings" tab="功能绑定">
        <n-space vertical :size="12">
          <n-card v-for="key of taskKeys" :key="key" size="small">
            <template #header>
              <n-text strong>{{ taskLabels[key] || key }}</n-text>
              <n-tag style="margin-left: 8px" size="small">{{ key }}</n-tag>
            </template>
            <n-form-item label="使用方案">
              <n-select
                :value="getBindingPlanId(key)"
                :options="planSelectOptions"
                :loading="bindingSaving === key"
                @update:value="(v) => onBind(key, v)"
              />
            </n-form-item>
            <template v-if="getBindingPlanId(key)">
              <n-text depth="3">
                绑定的方案中包含 API：
                <n-tag
                  v-for="api in (plans.find(p => p.id === getBindingPlanId(key))?.apis || [])"
                  :key="api.id"
                  style="margin: 2px"
                  size="small"
                  :type="api.enabled ? 'success' : 'default'"
                >
                  {{ api.name }} ({{ api.model_name }})
                </n-tag>
              </n-text>
            </template>
          </n-card>
        </n-space>
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
  </n-space>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { listModelApis, createModelApi, updateModelApi, deleteModelApi, testModelApi } from '../api/model-apis.js'
import { listPlans, createPlan, updatePlan, deletePlan } from '../api/plans.js'
import { listTaskBindings, updateTaskBinding, deleteTaskBinding } from '../api/task-bindings.js'

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
  ])
  apis.value = a.data
  plans.value = p.data
  bindings.value = b.data
})

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
    window.$message?.success('保存成功')
  } catch (e) {
    window.$message?.error(e.response?.data?.detail || '保存失败')
  } finally {
    apiSaving.value = false
  }
}

async function removeApi(id) {
  try {
    await deleteModelApi(id)
    const res = await listModelApis()
    apis.value = res.data
    window.$message?.success('删除成功')
  } catch (e) {
    window.$message?.error('删除失败')
  }
}

async function testApiConnection(id) {
  apiTesting.value = id
  try {
    const res = await testModelApi(id)
    window.$message?.[res.data.success ? 'success' : 'error'](
      res.data.success ? '连接成功' : `连接失败: ${res.data.error}`,
    )
  } catch (e) {
    window.$message?.error(`请求失败: ${e.message}`)
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
    window.$message?.success('保存成功')
  } catch (e) {
    window.$message?.error(e.response?.data?.detail || '保存失败')
  } finally {
    planSaving.value = false
  }
}

async function removePlan(id) {
  try {
    await deletePlan(id)
    const res = await listPlans()
    plans.value = res.data
    window.$message?.success('删除成功')
  } catch (e) {
    window.$message?.error('删除失败')
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
    window.$message?.success('绑定成功')
  } catch (e) {
    window.$message?.error(e.response?.data?.detail || '操作失败')
  } finally {
    bindingSaving.value = null
  }
}

function getBindingPlanId(taskKey) {
  const b = bindings.value.find(x => x.task_key === taskKey)
  return b?.plan_id || null
}
</script>
