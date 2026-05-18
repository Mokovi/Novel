<template>
  <div class="system-settings">
    <h2 class="page-title">系统设置</h2>

    <n-card title="生成配置" class="settings-card">
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

        <n-form-item label="自动分章目标字数">
          <n-text depth="3" class="form-hint">
            无限生成完成后，按此字数（字）为基准在段落边界处拆分内容为新章节。
          </n-text>
          <n-input-number
            v-model:value="settingsStore.autoSplitTargetWords"
            :min="500"
            :max="10000"
            :step="500"
            style="width: 200px"
          />
        </n-form-item>

        <n-button
          type="primary"
          :loading="settingsStore.loading"
          @click="handleSave"
        >
          保存设置
        </n-button>
      </n-space>
    </n-card>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useMessage, NCard, NSpace, NFormItem, NText, NInputNumber, NButton } from 'naive-ui'
import { useSettingsStore } from '../stores/settings.js'

const settingsStore = useSettingsStore()
const message = useMessage()

async function handleSave() {
  await settingsStore.saveGenerationSettings()
  message.success('设置已保存')
}

onMounted(() => {
  settingsStore.fetchGenerationSettings()
})
</script>

<style scoped>
.system-settings {
  max-width: 640px;
  margin: 0 auto;
}

.page-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 24px;
  color: var(--color-text-primary);
}

.settings-card {
  margin-bottom: 24px;
}

.form-hint {
  display: block;
  margin-bottom: 6px;
}
</style>
