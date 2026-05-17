<template>
  <n-config-provider :locale="zhCN" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-layout position="absolute" style="height: 100vh">
        <n-layout has-sider position="absolute">
          <!-- Sidebar -->
          <n-layout-sider bordered width="220" :native-scrollbar="false">
            <div class="sidebar-container">
              <!-- Brand -->
              <div class="sidebar-brand">
                <AppIcon name="logo" :size="26" class="brand-icon" />
                <span class="brand-text">作者工坊</span>
              </div>

              <!-- Navigation -->
              <n-menu
                :value="activeMenu"
                :options="menuOptions"
                @update:value="onMenuSelect"
                class="sidebar-menu"
              />

              <!-- Version footer -->
              <div class="sidebar-footer">
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-text depth="3" class="version-text">v{{ version }}</n-text>
                  </template>
                  当前项目版本
                </n-tooltip>
              </div>
            </div>
          </n-layout-sider>

          <!-- Main content -->
          <n-layout-content class="main-content">
            <router-view v-slot="{ Component, route: r }">
              <transition name="fade-slide" mode="out-in">
                <component :is="Component" :key="r.path" />
              </transition>
            </router-view>
          </n-layout-content>
        </n-layout>
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NConfigProvider, NMessageProvider, NLayout, NLayoutSider, NLayoutContent, NMenu, NText, NTooltip } from 'naive-ui'
import { zhCN } from 'naive-ui'
import { lightThemeOverrides } from './styles/naive-theme.js'
import AppIcon from './components/common/AppIcon.vue'
import DashboardIcon from './assets/icons/DashboardIcon.vue'
import OutlineIcon from './assets/icons/OutlineIcon.vue'
import EditorIcon from './assets/icons/EditorIcon.vue'
import WorldviewIcon from './assets/icons/WorldviewIcon.vue'
import SettingsIcon from './assets/icons/SettingsIcon.vue'

const router = useRouter()
const route = useRoute()

const themeOverrides = lightThemeOverrides

const activeMenu = computed(() => route.name || 'dashboard')

const iconSize = 20

const menuOptions = [
  {
    label: '工作台',
    key: 'dashboard',
    icon: () => h(DashboardIcon, { style: { width: `${iconSize}px`, height: `${iconSize}px` } }),
  },
  {
    label: '大纲视图',
    key: 'outline',
    icon: () => h(OutlineIcon, { style: { width: `${iconSize}px`, height: `${iconSize}px` } }),
  },
  {
    label: '章节编辑器',
    key: 'editor',
    icon: () => h(EditorIcon, { style: { width: `${iconSize}px`, height: `${iconSize}px` } }),
  },
  {
    label: '世界观',
    key: 'worldview',
    icon: () => h(WorldviewIcon, { style: { width: `${iconSize}px`, height: `${iconSize}px` } }),
  },
  {
    label: 'API 配置',
    key: 'settings',
    icon: () => h(SettingsIcon, { style: { width: `${iconSize}px`, height: `${iconSize}px` } }),
  },
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

<style scoped>
.sidebar-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 20px 12px;
  border-bottom: 1px solid #2a2520;
}

.brand-icon {
  color: var(--color-accent);
  flex-shrink: 0;
}

.brand-text {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-on-dark);
  letter-spacing: 2px;
}

.sidebar-menu {
  flex: 1;
  padding-top: 12px;
}

.sidebar-footer {
  padding: 12px 20px;
  border-top: 1px solid #2a2520;
}

.version-text {
  font-size: 12px;
  cursor: default;
  color: var(--color-text-on-dark-muted) !important;
}

.main-content {
  padding: 32px;
  overflow-y: auto;
}
</style>
