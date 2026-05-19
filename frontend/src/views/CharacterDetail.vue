<template>
  <div class="character-detail">
    <!-- Loading -->
    <div v-if="loading" class="loading-center">
      <n-spin size="medium" />
    </div>

    <!-- Not found -->
    <n-empty v-else-if="!character" description="人物不存在">
      <template #extra>
        <n-button size="small" @click="goBack">返回列表</n-button>
      </template>
    </n-empty>

    <!-- Detail form -->
    <template v-else>
      <div class="detail-header">
        <n-button quaternary size="small" @click="goBack">
          <template #icon>
            <n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M19 12H5M12 19l-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></n-icon>
          </template>
          返回
        </n-button>
        <h2>{{ character.name }}</h2>
        <div class="header-actions">
          <n-popconfirm @positive-click="handleDelete">
            <template #trigger>
              <n-button type="error" size="small" secondary>删除</n-button>
            </template>
            确定要删除「{{ character.name }}」吗？此操作不可撤销。
          </n-popconfirm>
        </div>
      </div>

      <n-card size="small" class="detail-card">
        <CharacterForm :character="character" @saved="onSaved" @cancel="goBack" />
      </n-card>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { getCharacter, deleteCharacter } from '../api/characters.js'
import CharacterForm from '../components/character/CharacterForm.vue'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const character = ref(null)
const loading = ref(false)

const bookId = computed(() => Number(route.params.bookId))

async function fetchCharacter() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const res = await getCharacter(id)
    character.value = res.data
  } catch {
    message.error('加载人物失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push(`/books/${bookId.value}/characters`)
}

async function handleDelete() {
  try {
    await deleteCharacter(character.value.id)
    message.success('已删除')
    goBack()
  } catch {
    message.error('删除失败')
  }
}

function onSaved() {
  fetchCharacter()
}

onMounted(fetchCharacter)
</script>

<style scoped>
.character-detail {
  max-width: 720px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.detail-header h2 {
  flex: 1;
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

.detail-card {
  margin-top: 8px;
}

.loading-center {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}
</style>
