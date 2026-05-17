<template>
  <n-config-provider :locale="zhCN">
    <n-message-provider>
      <n-layout position="absolute" style="height: 100vh">
        <n-layout has-sider position="absolute">
          <!-- Sidebar -->
          <n-layout-sider bordered width="200" :native-scrollbar="false">
            <n-menu
              :value="activeMenu"
              :options="menuOptions"
              @update:value="onMenuSelect"
              style="padding-top: 16px"
            />
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
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NConfigProvider, NMessageProvider, NLayout, NLayoutSider, NLayoutContent, NMenu } from 'naive-ui'
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

function onMenuSelect(key) {
  router.push({ name: key })
}
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>
