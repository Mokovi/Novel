<template>
  <n-config-provider :locale="zhCN" :theme-overrides="themeOverrides">
    <n-message-provider>
      <!-- Auth pages: no sidebar -->
      <template v-if="layout === 'auth'">
        <router-view />
      </template>

      <!-- Book select page: simple top bar -->
      <template v-else-if="layout === 'book-select'">
        <div class="book-select-layout">
          <div class="book-select-topbar">
            <div class="topbar-brand">
              <AppIcon name="logo" :size="22" class="brand-icon" />
              <span class="brand-text">作者工坊</span>
            </div>
            <div class="topbar-right">
              <span v-if="authStore.user" class="topbar-username">{{ authStore.user.username }}</span>
              <n-button size="tiny" quaternary @click="handleLogout">退出</n-button>
            </div>
          </div>
          <div class="book-select-content">
            <router-view />
          </div>
        </div>
      </template>

      <!-- Main app: full sidebar -->
      <template v-else>
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

                <!-- Book selector -->
                <BookSelector />

                <!-- Navigation -->
                <n-menu
                  :value="activeMenu"
                  :options="menuOptions"
                  @update:value="onMenuSelect"
                  class="sidebar-menu"
                />

                <!-- User + version + admin footer -->
                <div class="sidebar-footer">
                  <div class="footer-row">
                    <span v-if="authStore.user" class="username-text">{{ authStore.user.username }}</span>
                    <n-button size="tiny" quaternary @click="handleLogout">退出</n-button>
                  </div>
                  <div class="footer-row" style="margin-top: 4px">
                    <n-tag v-if="adminStore.isAdmin" size="tiny" type="warning" bordered style="margin-right: 6px">ADMIN</n-tag>
                    <n-tooltip trigger="hover">
                      <template #trigger>
                        <n-text depth="3" class="version-text">v{{ version }}</n-text>
                      </template>
                      当前项目版本
                    </n-tooltip>
                  </div>
                </div>
              </div>
            </n-layout-sider>

            <AdminLoginModal v-model:show="showAdminModal" @verified="onAdminVerified" @cancel="showAdminModal = false" />

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
      </template>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, h, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NButton,
  NConfigProvider,
  NLayout,
  NLayoutContent,
  NLayoutSider,
  NMenu,
  NMessageProvider,
  NTag,
  NText,
  NTooltip,
} from 'naive-ui'
import { zhCN } from 'naive-ui'
import { lightThemeOverrides } from './styles/naive-theme.js'
import AppIcon from './components/common/AppIcon.vue'
import BookSelector from './components/common/BookSelector.vue'
import { useAuthStore } from './stores/auth.js'
import { useAdminStore } from './stores/admin.js'
import { useBooksStore } from './stores/books.js'
import AdminLoginModal from './components/common/AdminLoginModal.vue'
import DashboardIcon from './assets/icons/DashboardIcon.vue'
import OutlineIcon from './assets/icons/OutlineIcon.vue'
import EditorIcon from './assets/icons/EditorIcon.vue'
import VariablesIcon from './assets/icons/VariablesIcon.vue'
import TemplateIcon from './assets/icons/TemplateIcon.vue'
import SettingsIcon from './assets/icons/SettingsIcon.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const adminStore = useAdminStore()
const booksStore = useBooksStore()

const themeOverrides = lightThemeOverrides

const version = ref('')
const showAdminModal = ref(false)

function handleKeydown(e) {
  if (e.ctrlKey && e.key === 'u') {
    e.preventDefault()
    showAdminModal.value = true
  }
}

function onAdminVerified() {
  // adminStore.isAdmin is already set by AdminLoginModal
}

const layout = computed(() => {
  return route.meta?.layout || 'app'
})

const activeMenu = computed(() => {
  // For book-scoped routes, map the route name back to menu keys
  const name = route.name
  if (name === 'dashboard') return 'dashboard'
  if (name === 'outline') return 'outline'
  if (name === 'editor') return 'editor'
  if (name === 'variables' || name === 'character-detail') return 'variables'
  if (name === 'templates') return 'templates'
  if (name === 'settings') return 'settings'
  return 'dashboard'
})

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
    label: '提示词变量',
    key: 'variables',
    icon: () => h(VariablesIcon, { style: { width: `${iconSize}px`, height: `${iconSize}px` } }),
  },
  {
    label: '模板库',
    key: 'templates',
    icon: () => h(TemplateIcon, { style: { width: `${iconSize}px`, height: `${iconSize}px` } }),
  },
  {
    label: '设置',
    key: 'settings',
    icon: () => h(SettingsIcon, { style: { width: `${iconSize}px`, height: `${iconSize}px` } }),
  },
]

function getCurrentBookId() {
  return Number(route.params.bookId) || booksStore.currentBook?.id || null
}

function onMenuSelect(key) {
  const bookId = getCurrentBookId()
  const routes = {
    dashboard: bookId ? `/books/${bookId}/dashboard` : '/books',
    outline: bookId ? `/books/${bookId}/outline` : '/books',
    editor: bookId ? `/books/${bookId}/editor` : '/books',
    variables: bookId ? `/books/${bookId}/variables` : '/books',
    templates: '/templates',
    settings: '/settings',
  }
  const path = routes[key]
  if (path) router.push(path)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  try {
    const res = await fetch('/api/v1/health')
    const data = await res.json()
    version.value = data.version || ''
  } catch { /* health endpoint not available */ }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
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

.footer-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username-text {
  font-size: 12px;
  color: var(--color-text-on-dark-muted);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

/* Book select layout */
.book-select-layout {
  min-height: 100vh;
  background: var(--color-bg-body);
}

.book-select-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-username {
  font-size: 13px;
  color: var(--color-text-muted);
}

.book-select-content {
  padding: 24px;
}
</style>
