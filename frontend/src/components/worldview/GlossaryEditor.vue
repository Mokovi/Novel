<template>
  <div class="glossary-editor">
    <div class="glossary-header">
      <n-button size="tiny" @click="addRow">
        <template #icon>
          <n-icon><svg viewBox="0 0 24 24" fill="none" width="14" height="14"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></n-icon>
        </template>
        添加词条
      </n-button>
    </div>

    <n-table v-if="items.length > 0" size="small" striped>
      <thead>
        <tr>
          <th style="width: 30%">术语</th>
          <th style="width: 55%">定义</th>
          <th style="width: 15%">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in items" :key="index">
          <td>
            <n-input
              v-model:value="item.term"
              placeholder="输入术语"
              size="small"
              @update:value="emitUpdate"
            />
          </td>
          <td>
            <n-input
              v-model:value="item.definition"
              placeholder="输入定义"
              size="small"
              @update:value="emitUpdate"
            />
          </td>
          <td>
            <n-button size="tiny" quaternary circle type="error" @click="removeRow(index)">
              <template #icon>
                <n-icon><svg viewBox="0 0 24 24" fill="none" width="14" height="14"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></n-icon>
              </template>
            </n-button>
          </td>
        </tr>
      </tbody>
    </n-table>

    <n-empty v-else description="暂无词条，点击上方按钮添加" />
  </div>
</template>

<script setup>
const props = defineProps({
  items: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:items'])

function emitUpdate() {
  emit('update:items', [...props.items])
}

function addRow() {
  const updated = [...props.items, { term: '', definition: '' }]
  emit('update:items', updated)
}

function removeRow(index) {
  const updated = props.items.filter((_, i) => i !== index)
  emit('update:items', updated)
}
</script>

<style scoped>
.glossary-header {
  margin-bottom: 12px;
}
</style>
