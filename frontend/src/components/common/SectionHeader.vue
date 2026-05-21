<template>
  <div class="section-header-accent">
    <div class="section-header-left">
      <div class="section-bar" />
      <h3 class="section-title">{{ title }}</h3>
      <span v-if="tag" class="section-tag">{{ tag }}</span>
    </div>
    <div class="section-header-right">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  tag: { type: String, default: '' },
})
</script>

<style scoped>
.section-header-accent {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-bar {
  width: 3px;
  height: 22px;
  border-radius: 2px;
  background: var(--color-accent);
  flex-shrink: 0;
}

.section-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.section-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #e8e6e1;
  color: #666;
  font-family: var(--font-mono, 'SF Mono', 'Fira Code', monospace);
}

.section-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
