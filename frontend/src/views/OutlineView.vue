<template>
  <n-space vertical :size="16">
    <n-h1>大纲视图</n-h1>

    <n-space>
      <n-button type="primary" @click="showCreateVolume = true">创建卷</n-button>
      <n-button @click="showCreateChapter = true">创建章节</n-button>
    </n-space>

    <!-- Volume list -->
    <n-collapse v-if="store.volumes.length">
      <n-collapse-item
        v-for="vol in store.volumes"
        :key="vol.id"
        :title="vol.title"
        :name="String(vol.id)"
      >
        <template #header-extra>
          <n-tag>{{ vol.chapters?.length || 0 }} 章</n-tag>
        </template>

        <n-list v-if="chaptersByVolume(vol.id).length">
          <n-list-item
            v-for="ch in chaptersByVolume(vol.id)"
            :key="ch.id"
            clickable
            @click="$router.push(`/editor/${ch.id}`)"
          >
            <n-thing :title="ch.title" :description="ch.summary">
              <template #footer>
                <n-space>
                  <n-tag size="small" :type="statusType(ch.status)">
                    {{ statusLabel(ch.status) }}
                  </n-tag>
                  <n-text depth="3">{{ ch.word_count }} 字</n-text>
                </n-space>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
        <n-empty v-else description="该卷下暂无章节" />
      </n-collapse-item>
    </n-collapse>
    <n-empty v-else description="暂无卷，请先创建" />

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
  </n-space>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useChaptersStore } from '../stores/chapters.js'
import { createVolume, createChapter } from '../api/chapters.js'

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

onMounted(async () => {
  await store.fetchVolumes()
  await store.fetchChapters()
})
</script>
