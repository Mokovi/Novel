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

              <!-- Book Selector -->
              <BookSelector />

              <!-- Navigation -->
              <n-menu
                :value="activeMenu"
                :options="menuOptions"
                @update:value="onMenuSelect"
                class="sidebar-menu"
              />

              <!-- Version footer -->
              <div class="sidebar-footer">
                <div class="footer-row">
                  <n-tooltip trigger="hover">
                    <template #trigger>
                      <n-text depth="3" class="version-text">v{{ version }}</n-text>
                    </template>
                    当前项目版本
                  </n-tooltip>
                  <n-tag v-if="adminStore.isAdmin" type="warning" size="tiny" class="admin-badge">ADMIN</n-tag>
                </div>
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

        <AdminLoginModal v-model:show="showAdminModal" />
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, h, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NConfigProvider, NMessageProvider, NLayout, NLayoutSider, NLayoutContent, NMenu, NTag, NText, NTooltip } from 'naive-ui'
import { zhCN } from 'naive-ui'
import { lightThemeOverrides } from './styles/naive-theme.js'
import AppIcon from './components/common/AppIcon.vue'
import BookSelector from './components/common/BookSelector.vue'
import AdminLoginModal from './components/common/AdminLoginModal.vue'
import { useAdminStore } from './stores/admin.js'
import { useBooksStore } from './stores/books.js'
import DashboardIcon from './assets/icons/DashboardIcon.vue'
import OutlineIcon from './assets/icons/OutlineIcon.vue'
import EditorIcon from './assets/icons/EditorIcon.vue'
import WorldviewIcon from './assets/icons/WorldviewIcon.vue'
import CharacterIcon from './assets/icons/CharacterIcon.vue'
import TemplateIcon from './assets/icons/TemplateIcon.vue'
import SettingsIcon from './assets/icons/SettingsIcon.vue'

const router = useRouter()
const route = useRoute()
const booksStore = useBooksStore()

const themeOverrides = lightThemeOverrides

const activeMenu = computed(() => {
  const name = route.name
  if (!name) return 'dashboard'
  if (name === 'book-outline') return 'outline'
  if (name === 'book-editor') return 'editor'
  if (name === 'book-worldview') return 'worldview'
  if (name === 'book-characters' || name === 'book-character-detail') return 'characters'
  return name
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
    label: '世界观',
    key: 'worldview',
    icon: () => h(WorldviewIcon, { style: { width: `${iconSize}px`, height: `${iconSize}px` } }),
  },
  {
    label: '人物',
    key: 'characters',
    icon: () => h(CharacterIcon, { style: { width: `${iconSize}px`, height: `${iconSize}px` } }),
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

const version = ref('')
const adminStore = useAdminStore()
const showAdminModal = ref(false)

function handleKeydown(e) {
  if (e.ctrlKey && e.key === 'u') {
    e.preventDefault()
    showAdminModal.value = true
  }
}

function onMenuSelect(key) {
  const bookId = booksStore.currentBookId
  const bookScoped = {
    outline: 'book-outline',
    editor: 'book-editor',
    worldview: 'book-worldview',
    characters: 'book-characters',
  }
  if (bookScoped[key] && bookId) {
    router.push({ name: bookScoped[key], params: { bookId } })
  } else {
    router.push({ name: key })
  }
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  // Ensure current book is loaded
  try {
    await booksStore.ensureCurrentBook()
  } catch { /* fallback */ }
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

.version-text {
  font-size: 12px;
  cursor: default;
  color: var(--color-text-on-dark-muted) !important;
}

.admin-badge {
  font-size: 10px;
  letter-spacing: 1px;
}

.main-content {
  padding: 32px;
  overflow-y: auto;
}
</style>
