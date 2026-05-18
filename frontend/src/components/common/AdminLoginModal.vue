<template>
  <n-modal
    :show="show"
    preset="card"
    title="管理员验证"
    style="max-width: 400px"
    :mask-closable="false"
    @update:show="$emit('update:show', $event)"
  >
    <n-space vertical :size="16">
      <n-input
        v-model:value="password"
        type="password"
        placeholder="请输入管理员密码"
        @keyup.enter="handleSubmit"
      />
      <n-space justify="end">
        <n-button @click="$emit('cancel')">取消</n-button>
        <n-button type="primary" :loading="loading" @click="handleSubmit">验证</n-button>
      </n-space>
      <n-alert v-if="error" type="error" :show-icon="false">
        {{ error }}
      </n-alert>
    </n-space>
  </n-modal>
</template>

<script setup>
import { ref } from 'vue'
import { NModal, NSpace, NInput, NButton, NAlert } from 'naive-ui'
import { useAdminStore } from '../../stores/admin.js'

defineProps({ show: Boolean })
const emit = defineEmits(['update:show', 'verified', 'cancel'])

const adminStore = useAdminStore()
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    const ok = await adminStore.verify(password.value)
    if (ok) {
      password.value = ''
      emit('update:show', false)
      emit('verified')
    } else {
      error.value = '密码错误'
    }
  } catch (e) {
    error.value = '验证失败，请检查网络连接'
  } finally {
    loading.value = false
  }
}
</script>
