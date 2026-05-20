<template>
  <n-dropdown
    trigger="manual"
    placement="bottom-start"
    :show="visible"
    :x="posX"
    :y="posY"
    :options="menuOptions"
    @select="onSelect"
    @clickoutside="hide"
  />
</template>

<script setup>
import { ref, computed } from 'vue'
import { NDropdown } from 'naive-ui'

const props = defineProps({
  options: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['select'])

const visible = ref(false)
const posX = ref(0)
const posY = ref(0)

const menuOptions = computed(() => props.options)

function show(x, y) {
  posX.value = x
  posY.value = y
  visible.value = true
}

function hide() {
  visible.value = false
}

function onSelect(key) {
  hide()
  emit('select', key)
}

defineExpose({ show, hide })
</script>
