<template>
  <component :is="iconComponent" :style="iconStyle" class="app-icon" />
</template>

<script setup>
import { computed } from 'vue'
import DashboardIcon from '../../assets/icons/DashboardIcon.vue'
import OutlineIcon from '../../assets/icons/OutlineIcon.vue'
import EditorIcon from '../../assets/icons/EditorIcon.vue'
import SettingsIcon from '../../assets/icons/SettingsIcon.vue'
import LogoIcon from '../../assets/icons/LogoIcon.vue'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 18 },
})

const iconMap = { dashboard: DashboardIcon, outline: OutlineIcon, editor: EditorIcon, settings: SettingsIcon, logo: LogoIcon }

const iconComponent = computed(() => iconMap[props.name] || null)

const iconStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  display: 'inline-block',
  verticalAlign: 'middle',
}))
</script>

<style scoped>
.app-icon {
  display: inline-block;
  flex-shrink: 0;
}
</style>
