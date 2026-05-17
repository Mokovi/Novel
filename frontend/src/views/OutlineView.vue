<template>
  <div class="outline">
    <h1 class="page-title">大纲视图</h1>

    <!-- Toolbar -->
    <div class="toolbar">
      <n-button type="primary" @click="showCreateVolume = true">创建卷</n-button>
      <n-button @click="showCreateChapter = true">创建章节</n-button>
      <n-divider vertical />
      <n-button @click="handleBatchDownload">批量下载</n-button>
    </div>

    <!-- Volume list -->
    <div v-if="store.volumes.length" class="volume-list">
      <div
        v-for="vol in store.volumes"
        :key="vol.id"
        class="volume-section"
      >
        <h2 class="volume-title">
          <span class="volume-title-text">{{ vol.title }}</span>
          <div class="volume-meta">
            <span class="chapter-count">{{ chaptersByVolume(vol.id).length }} 章</span>
            <n-popconfirm @positive-click="handleDeleteVolume(vol.id)">
              <template #trigger>
                <n-button size="tiny" text class="delete-btn" @click.stop>删除卷</n-button>
              </template>
              确定删除此卷及其下所有章节？
            </n-popconfirm>
          </div>
        </h2>

        <p v-if="vol.description" class="volume-desc">{{ vol.description }}</p>

        <div v-if="chaptersByVolume(vol.id).length" class="chapter-list">
          <div
            v-for="ch in chaptersByVolume(vol.id)"
            :key="ch.id"
            class="chapter-card"
            :class="[`status-${ch.status}`]"
            @click="$router.push(`/editor/${ch.id}`)"
          >
            <div class="chapter-body">
              <h3 class="chapter-title">{{ ch.title }}</h3>
              <p v-if="ch.summary" class="chapter-summary">{{ ch.summary }}</p>
              <div class="chapter-footer">
                <n-tag size="small" :type="statusType(ch.status)">
                  {{ statusLabel(ch.status) }}
                </n-tag>
                <span class="word-count">{{ ch.word_count }} 字</span>
              </div>
            </div>
            <div class="chapter-actions" @click.stop>
              <n-button size="tiny" @click="handleGenerateChapter(ch)">生成</n-button>
              <n-button size="tiny" @click="handleDownloadChapter(ch)">下载</n-button>
              <n-popconfirm @positive-click="handleDeleteChapter(ch.id, ch.volume_id)">
                <template #trigger>
                  <n-button size="tiny" text class="delete-btn">删除</n-button>
                </template>
                确定删除此章节？
              </n-popconfirm>
            </div>
          </div>
        </div>
        <div v-else class="empty-chapters">
          <n-empty description="该卷下暂无章节" size="small" />
        </div>
      </div>
    </div>
    <div v-else class="empty-volume">
      <n-empty description="暂无卷，请先创建" />
    </div>

    <!-- Create Volume Modal -->
    <n-modal v-model:show="showCreateVolume" title="创建卷" preset="card" style="width: 480px">
      <n-form>
        <n-form-item label="卷标题">
          <n-input v-model:value="newVolume.title" placeholder="如：第一卷" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="newVolume.description" type="textarea" rows="3" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button type="primary" @click="handleCreateVolume">创建</n-button>
      </template>
    </n-modal>

    <!-- Create Chapter Modal -->
    <n-modal v-model:show="showCreateChapter" title="创建章节" preset="card" style="width: 520px">
      <n-form>
        <n-form-item label="所属卷">
          <n-select
            v-model:value="newChapter.volume_id"
            :options="volumeOptions"
            placeholder="选择卷"
          />
        </n-form-item>
        <n-form-item label="章节标题">
          <n-input v-model:value="newChapter.title" placeholder="如：第一章 开端" />
        </n-form-item>
        <n-form-item label="摘要">
          <n-input v-model:value="newChapter.summary" type="textarea" rows="3" placeholder="本章摘要" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button type="primary" @click="handleCreateChapter">创建</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChaptersStore } from '../stores/chapters.js'
import { createVolume, createChapter, deleteChapter, deleteVolume, downloadChapter, downloadAllChapters } from '../api/chapters.js'

const router = useRouter()
const store = useChaptersStore()

const showCreateVolume = ref(false)
const showCreateChapter = ref(false)

const newVolume = ref({ title: '', description: '' })
const newChapter = ref({ volume_id: null, title: '', summary: '' })

const volumeOptions = computed(() =>
  store.volumes.map(v => ({ label: v.title, value: v.id }))
)

const chaptersByVolume = (volId) =>
  store.chapters.filter(c => c.volume_id === volId)

const statusType = (s) =>
  ({ pending: 'default', generating: 'warning', completed: 'success' }[s] || 'default')

const statusLabel = (s) =>
  ({ pending: '待生成', generating: '生成中', completed: '已完成' }[s] || s)

async function handleCreateVolume() {
  await createVolume(newVolume.value)
  newVolume.value = { title: '', description: '' }
  showCreateVolume.value = false
  await store.fetchVolumes()
}

async function handleCreateChapter() {
  await createChapter(newChapter.value)
  newChapter.value = { volume_id: null, title: '', summary: '' }
  showCreateChapter.value = false
  await store.fetchChapters()
}

async function handleDeleteVolume(id) {
  await deleteVolume(id)
  await store.fetchVolumes()
  await store.fetchChapters()
}

async function handleDeleteChapter(id, volumeId) {
  await deleteChapter(id)
  await store.fetchChapters(volumeId)
}

function handleGenerateChapter(ch) {
  router.push(`/editor/${ch.id}?generate=1`)
}

async function handleDownloadChapter(ch) {
  const res = await downloadChapter(ch.id)
  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = `${ch.title || 'chapter'}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

async function handleBatchDownload() {
  const res = await downloadAllChapters()
  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = 'chapters.zip'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  await store.fetchVolumes()
  await store.fetchChapters()
})
</script>

<style scoped>
.outline {
  max-width: 860px;
  margin: 0 auto;
}

.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 20px;
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

/* Volume */
.volume-section {
  margin-bottom: 28px;
  animation: fade-in-up 0.4s ease both;
}

.volume-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0 6px;
}

.volume-title-text {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-accent-dark);
  letter-spacing: 1px;
}

.volume-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chapter-count {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.volume-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
  line-height: 1.5;
}

/* Chapter list */
.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chapter-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  cursor: pointer;
  border-left: 3px solid var(--color-border);
  transition: background var(--transition-fast), box-shadow var(--transition-fast);
  animation: fade-in-up 0.35s ease both;
}

.chapter-card:hover {
  background: rgba(201, 169, 78, 0.04);
  box-shadow: var(--shadow-sm);
}

.chapter-card.status-pending {
  border-left-color: var(--color-accent);
}

.chapter-card.status-generating {
  border-left-color: var(--color-warning);
}

.chapter-card.status-completed {
  border-left-color: var(--color-success);
}

.chapter-body {
  flex: 1;
  min-width: 0;
}

.chapter-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px;
}

.chapter-summary {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 8px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.chapter-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.word-count {
  font-size: 12px;
  color: var(--color-text-muted);
}

.chapter-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.delete-btn {
  color: var(--color-text-muted) !important;
  font-size: 12px;
}

.delete-btn:hover {
  color: var(--color-error) !important;
}

.empty-chapters {
  padding: 12px 0;
}

.empty-volume {
  margin-top: 60px;
}
</style>
