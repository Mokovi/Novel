<template>
  <n-config-provider :locale="zhCN">
    <n-message-provider>
      <n-layout position="absolute" style="height: 100vh">
        <n-layout has-sider position="absolute">
          <!-- Sidebar -->
          <n-layout-sider bordered width="200" :native-scrollbar="false">
            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column">
              <n-menu
                :value="activeMenu"
                :options="menuOptions"
                @update:value="onMenuSelect"
                style="flex: 1; padding-top: 16px"
              />
              <div style="padding: 12px 24px; border-top: 1px solid var(--n-border-color); background: var(--n-color)">
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-text depth="3" style="font-size: 12px; cursor: default">v{{ version }}</n-text>
                  </template>
                  当前项目版本
                </n-tooltip>
              </div>
            </div>
          </n-layout-sider>

          <!-- Main content -->
          <n-layout-content style="padding: 24px; overflow-y: auto">
            <router-view />
          </n-layout-content>
        </n-layout>
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NConfigProvider, NMessageProvider, NLayout, NLayoutSider, NLayoutContent, NMenu, NText, NTooltip } from 'naive-ui'
import { zhCN } from 'naive-ui'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => route.name || 'dashboard')

const menuOptions = [
  { label: '工作台', key: 'dashboard', icon: () => '📋' },
  { label: '大纲视图', key: 'outline', icon: () => '📑' },
  { label: '章节编辑器', key: 'editor', icon: () => '✏️' },
  { label: 'API 配置', key: 'settings', icon: () => '⚙️' },
]

const version = ref('')

function onMenuSelect(key) {
  router.push({ name: key })
}

onMounted(async () => {
  try {
    const res = await fetch('/api/v1/health')
    const data = await res.json()
    version.value = data.version || ''
  } catch { /* health endpoint not available */ }
})
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>
