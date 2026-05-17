<template>
  <n-space vertical :size="16">
    <n-h1>API Key 配置</n-h1>
    <n-p>为每个任务类型配置独立的 AI 模型和 API Key。</n-p>

    <n-card v-for="route in routes" :key="route.task_key" :title="taskLabel(route.task_key)">
      <n-form>
        <n-form-item label="提供商">
          <n-select
            v-model:value="route.provider"
            :options="providerOptions"
            @update:value="markChanged(route.task_key)"
          />
        </n-form-item>
        <n-form-item label="模型">
          <n-input
            v-model:value="route.model_name"
            placeholder="如: gpt-4o-mini"
            @update:value="markChanged(route.task_key)"
          />
        </n-form-item>
        <n-form-item label="API Base URL">
          <n-input
            v-model:value="route.api_base_url"
            placeholder="留空使用默认"
            @update:value="markChanged(route.task_key)"
          />
        </n-form-item>
        <n-form-item label="API Key">
          <n-input
            v-model:value="route.api_key"
            type="password"
            show-password-on="click"
            :placeholder="route.api_key_mask || '输入 API Key'"
            @update:value="markChanged(route.task_key)"
          />
        </n-form-item>
        <n-space>
          <n-button
            type="primary"
            :loading="saving === route.task_key"
            @click="handleSave(route)"
          >
            保存
          </n-button>
          <n-button
            :loading="testing === route.task_key"
            @click="handleTest(route)"
          >
            测试连接
          </n-button>
        </n-space>
        <n-alert v-if="testResults[route.task_key]" :type="testResults[route.task_key].success ? 'success' : 'error'" style="margin-top: 12px">
          {{ testResults[route.task_key].message }}
        </n-alert>
      </n-form>
    </n-card>
  </n-space>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listModelRoutes, updateModelRoute, testModelRoute } from '../api/settings.js'

const routes = ref([])
const changed = ref(new Set())
const saving = ref(null)
const testing = ref(null)
const testResults = ref({})

const providerOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'Anthropic', value: 'anthropic' },
]

const taskLabels = {
  outline_design: '大纲设计',
  chapter_writing: '章节写作',
  character_design: '人物设计',
  worldbuilding: '世界观构建',
  revision: '润色修改',
}

function taskLabel(key) {
  return taskLabels[key] || key
}

function markChanged(taskKey) {
  changed.value.add(taskKey)
}

async function handleSave(route) {
  saving.value = route.task_key
  try {
    const { task_key, ...data } = route
    await updateModelRoute(task_key, data)
    changed.value.delete(task_key)
    window.$message?.success('保存成功')
  } catch (e) {
    window.$message?.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = null
  }
}

async function handleTest(route) {
  testing.value = route.task_key
  try {
    const res = await testModelRoute(route.task_key)
    testResults.value[route.task_key] = {
      success: res.data.success,
      message: res.data.success ? '连接成功' : `失败: ${res.data.error}`,
    }
  } catch (e) {
    testResults.value[route.task_key] = {
      success: false,
      message: `请求失败: ${e.message}`,
    }
  } finally {
    testing.value = null
  }
}

onMounted(async () => {
  const res = await listModelRoutes()
  routes.value = res.data.map((r) => ({
    ...r,
    api_key: '', // don't populate the masked key into input
  }))
})
</script>
