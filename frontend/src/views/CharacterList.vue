<template>
  <div class="character-list">
    <!-- Header -->
    <div class="list-header">
      <h2>人物管理</h2>
      <div class="header-actions">
        <n-button type="primary" size="small" @click="showCreate = true">
          <template #icon>
            <n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></n-icon>
          </template>
          新建人物
        </n-button>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <n-radio-group v-model:value="roleFilter" size="small" @update:value="onFilterChange">
        <n-radio-button value="">全部</n-radio-button>
        <n-radio-button value="protagonist">主角</n-radio-button>
        <n-radio-button value="antagonist">反派</n-radio-button>
        <n-radio-button value="supporting">配角</n-radio-button>
        <n-radio-button value="minor">龙套</n-radio-button>
      </n-radio-group>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-center">
      <n-spin size="medium" />
    </div>

    <!-- Empty state -->
    <n-empty v-else-if="characters.length === 0" description="暂无人物，点击「新建人物」开始创建" class="empty-state" />

    <!-- Character cards -->
    <div v-else class="card-grid">
      <n-card
        v-for="c in characters"
        :key="c.id"
        class="character-card"
        hoverable
        size="small"
        @click="openDetail(c.id)"
      >
        <div class="card-content">
          <div class="card-top">
            <span class="character-name">{{ c.name }}</span>
            <n-tag v-if="c.role_type" :type="roleTagType(c.role_type)" size="tiny">
              {{ roleLabel(c.role_type) }}
            </n-tag>
          </div>
          <div v-if="c.aliases" class="card-aliases">{{ c.aliases }}</div>
          <div class="card-desc">{{ c.description || '暂无描述' }}</div>
          <div class="card-footer">
            <n-tag v-if="c.status === 'active'" size="tiny" type="success">活跃</n-tag>
            <n-tag v-else-if="c.status === 'deceased'" size="tiny" type="error">已故</n-tag>
            <n-tag v-else size="tiny" type="warning">{{ c.status }}</n-tag>
            <span class="card-time">{{ formatDate(c.updated_at) }}</span>
          </div>
        </div>
      </n-card>
    </div>

    <!-- Create modal -->
    <n-modal v-model:show="showCreate" preset="card" title="新建人物" style="width: 520px" segmented>
      <CharacterForm @saved="onCreated" @cancel="showCreate = false" />
    </n-modal>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { listCharacters } from '../api/characters.js'
import CharacterForm from '../components/character/CharacterForm.vue'

const router = useRouter()
const message = useMessage()

const characters = ref([])
const loading = ref(false)
const roleFilter = ref('')
const showCreate = ref(false)

const roleTagType = (type) => {
  const map = { protagonist: 'success', antagonist: 'error', supporting: 'info', minor: 'default' }
  return map[type] || 'default'
}

const roleLabel = (type) => {
  const map = { protagonist: '主角', antagonist: '反派', supporting: '配角', minor: '龙套' }
  return map[type] || type
}

const formatDate = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN')
}

async function fetchCharacters() {
  loading.value = true
  try {
    const params = {}
    if (roleFilter.value) params.role_type = roleFilter.value
    const res = await listCharacters(params)
    characters.value = res.data
  } catch {
    message.error('加载人物列表失败')
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  fetchCharacters()
}

function openDetail(id) {
  router.push({ name: 'character-detail', params: { id } })
}

function onCreated() {
  showCreate.value = false
  fetchCharacters()
  message.success('人物创建成功')
}

onMounted(fetchCharacters)
</script>

<style scoped>
.character-list {
  max-width: 960px;
  margin: 0 auto;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.list-header h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-bar {
  margin-bottom: 20px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.character-card {
  cursor: pointer;
}

.character-card :deep(.n-card__content) {
  padding: 16px;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.character-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.card-aliases {
  font-size: 12px;
  color: var(--color-text-muted, #999);
}

.card-desc {
  font-size: 13px;
  color: var(--color-text-secondary, #666);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.card-time {
  font-size: 11px;
  color: var(--color-text-muted, #999);
}

.loading-center {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.empty-state {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
