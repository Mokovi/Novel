<template>
  <div class="object-editor">
    <template v-for="(val, key) in value" :key="key">
      <div class="field-row">
        <label class="field-label">{{ key }}</label>
        <div class="field-control">
          <!-- Nested object -->
          <template v-if="val !== null && typeof val === 'object' && !Array.isArray(val)">
            <n-collapse>
              <n-collapse-item :title="key" :name="key">
                <ObjectEditor :value="val" nested @update:value="onNestedUpdate(key, $event)" />
              </n-collapse-item>
            </n-collapse>
          </template>

          <!-- Array -->
          <template v-else-if="Array.isArray(val)">
            <ArrayEditor :value="val" @update:value="onUpdate(key, $event)" />
          </template>

          <!-- String - textarea for longer text, input for short -->
          <template v-else-if="typeof val === 'string'">
            <n-input
              v-if="isLongText(val)"
              v-model:value="value[key]"
              type="textarea"
              :rows="4"
              :placeholder="`输入${key}`"
              @update:value="emitUpdate"
            />
            <n-input
              v-else
              v-model:value="value[key]"
              :placeholder="`输入${key}`"
              @update:value="emitUpdate"
            />
          </template>

          <!-- Number or other -->
          <template v-else>
            <n-input
              v-model:value="value[key]"
              :placeholder="`输入${key}`"
              @update:value="emitUpdate"
            />
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
  value: { type: Object, default: () => ({}) },
  nested: { type: Boolean, default: false },
})
const emit = defineEmits(['update:value'])

function isLongText(str) {
  return str.length > 80 || (str.match(/\n/g) || []).length > 1
}

function emitUpdate() {
  emit('update:value', { ...props.value })
}

function onUpdate(key, newVal) {
  props.value[key] = newVal
  emitUpdate()
}

function onNestedUpdate(key, newVal) {
  props.value[key] = newVal
  emitUpdate()
}
</script>

<style scoped>
.object-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.field-label {
  min-width: 100px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary, #666);
  padding-top: 6px;
  flex-shrink: 0;
}

.field-control {
  flex: 1;
  min-width: 0;
}
</style>
