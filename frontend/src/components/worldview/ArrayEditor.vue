<template>
  <div class="array-editor">
    <template v-if="value.length > 0">
      <!-- Array of objects -->
      <template v-if="isArrayOfObjects">
        <n-collapse>
          <n-collapse-item
            v-for="(item, index) in value"
            :key="index"
            :title="`#${index + 1} ${getItemTitle(item)}`"
            :name="String(index)"
          >
            <div class="array-item">
              <ObjectEditor :value="item" nested @update:value="onItemUpdate(index, $event)" />
              <n-button size="tiny" quaternary type="error" class="remove-btn" @click="removeItem(index)">
                <template #icon>
                  <n-icon><svg viewBox="0 0 24 24" fill="none" width="14" height="14"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></n-icon>
                </template>
                删除
              </n-button>
            </div>
          </n-collapse-item>
        </n-collapse>
      </template>

      <!-- Array of strings -->
      <template v-else>
        <div v-for="(item, index) in value" :key="index" class="string-item">
          <n-input
            v-model:value="value[index]"
            size="small"
            @update:value="emitUpdate"
          />
          <n-button size="tiny" quaternary circle type="error" @click="removeItem(index)">
            <template #icon>
              <n-icon><svg viewBox="0 0 24 24" fill="none" width="14" height="14"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></n-icon>
            </template>
          </n-button>
        </div>
      </template>
    </template>

    <!-- Add button -->
    <n-button size="tiny" class="add-btn" @click="addItem">
      <template #icon>
        <n-icon><svg viewBox="0 0 24 24" fill="none" width="14" height="14"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></n-icon>
      </template>
      添加条目
    </n-button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ObjectEditor from './ObjectEditor.vue'

const props = defineProps({
  value: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:value'])

const isArrayOfObjects = computed(() => {
  return props.value.length > 0 && typeof props.value[0] === 'object' && !Array.isArray(props.value[0])
})

function getItemTitle(item) {
  if (item.name || item.名称) return item.name || item.名称
  return ''
}

function emitUpdate() {
  emit('update:value', [...props.value])
}

function onItemUpdate(index, newVal) {
  props.value[index] = newVal
  emitUpdate()
}

function addItem() {
  const updated = [...props.value]
  if (isArrayOfObjects.value) {
    updated.push({ name: '', 名称: '', description: '', 描述: '' })
  } else {
    updated.push('')
  }
  emit('update:value', updated)
}

function removeItem(index) {
  const updated = props.value.filter((_, i) => i !== index)
  emit('update:value', updated)
}
</script>

<style scoped>
.array-item {
  padding: 8px 0;
}

.remove-btn {
  margin-top: 8px;
}

.string-item {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.string-item .n-input {
  flex: 1;
}

.add-btn {
  margin-top: 8px;
}
</style>
