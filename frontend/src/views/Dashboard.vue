<template>
  <div class="dashboard">
    <!-- Hero -->
    <section class="hero">
      <h1 class="hero-title">作者工坊</h1>
      <p class="hero-subtitle">人机协作的长篇叙事创作空间</p>
    </section>

    <!-- Stats -->
    <section class="stats-grid">
      <div
        v-for="(stat, i) in stats"
        :key="stat.label"
        class="stat-card"
        :style="{ animationDelay: `${i * 0.1}s` }"
      >
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-label">{{ stat.label }}</div>
      </div>
    </section>

    <!-- Quick start -->
    <section class="quick-start">
      <h2 class="section-title">快速开始</h2>
      <div class="quick-cards">
        <div class="quick-card" @click="goToOutline">
          <div class="quick-card-icon">
            <OutlineIcon />
          </div>
          <div class="quick-card-content">
            <h3>管理大纲</h3>
            <p>创建卷和章节，规划故事结构</p>
          </div>
        </div>
        <div class="quick-card" @click="goToEditor">
          <div class="quick-card-icon">
            <EditorIcon />
          </div>
          <div class="quick-card-content">
            <h3>开始写作</h3>
            <p>编辑章节内容或使用 AI 生成</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChaptersStore } from '../stores/chapters.js'
import OutlineIcon from '../assets/icons/OutlineIcon.vue'
import EditorIcon from '../assets/icons/EditorIcon.vue'

const router = useRouter()
const route = useRoute()
const store = useChaptersStore()

const bookId = computed(() => Number(route.params.bookId))

const stats = computed(() => [
  { label: '卷', value: store.volumes.length },
  { label: '章节', value: store.chapters.length },
  { label: '已完成', value: store.chapters.filter(c => c.status === 'completed').length },
  { label: '总字数', value: totalWords.value },
])

const totalWords = computed(() =>
  store.chapters.reduce((sum, c) => sum + (c.word_count || 0), 0)
)

function goToOutline() {
  router.push(`/books/${bookId.value}/outline`)
}

function goToEditor() {
  if (store.chapters.length) {
    router.push(`/books/${bookId.value}/editor/${store.chapters[0].id}`)
  } else {
    router.push(`/books/${bookId.value}/outline`)
  }
}

onMounted(async () => {
  await store.fetchVolumes(bookId.value)
  await store.fetchChapters(bookId.value)
})
</script>

<style scoped>
.dashboard {
  max-width: 800px;
  margin: 0 auto;
}

/* Hero */
.hero {
  margin-bottom: 36px;
  animation: fade-in-up 0.5s ease both;
}

.hero-title {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 8px;
  letter-spacing: 3px;
}

.hero-subtitle {
  font-family: var(--font-body);
  font-size: 16px;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 40px;
}

.stat-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px 16px;
  text-align: center;
  cursor: default;
  animation: fade-in-up 0.4s ease both;
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.stat-value {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--color-accent);
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-family: var(--font-ui);
}

/* Quick start */
.section-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 16px;
}

.quick-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  cursor: pointer;
  transition: transform var(--transition-base), box-shadow var(--transition-base);
  animation: fade-in-up 0.4s ease both;
  animation-delay: 0.3s;
}

.quick-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-card-hover);
}

.quick-card-icon {
  width: 40px;
  height: 40px;
  color: var(--color-accent);
  flex-shrink: 0;
}

.quick-card-icon svg {
  width: 100%;
  height: 100%;
}

.quick-card-content h3 {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px;
}

.quick-card-content p {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0;
}
</style>
