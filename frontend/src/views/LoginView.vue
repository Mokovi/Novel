<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-title">作者工坊</h1>
        <p class="auth-subtitle">登录你的账户</p>
      </div>
      <n-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="form.username" placeholder="输入用户名" :disabled="loading" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input
            v-model:value="form.password"
            type="password"
            placeholder="输入密码"
            :disabled="loading"
            @keyup.enter="handleLogin"
          />
        </n-form-item>
        <n-button type="primary" block :loading="loading" attr-type="submit" size="large">
          {{ loading ? '登录中...' : '登录' }}
        </n-button>
      </n-form>
      <div class="auth-footer">
        <span>还没有账户？</span>
        <n-button text type="primary" @click="$router.push('/register')">
          注册
        </n-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NForm, NFormItem, NInput, useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    message.success('登录成功')
    const savedBookId = localStorage.getItem('current_book_id')
    if (savedBookId) {
      router.push(`/books/${savedBookId}/outline`)
    } else {
      router.push('/books')
    }
  } catch (e) {
    const detail = e.response?.data?.detail || '登录失败'
    message.error(detail)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--color-bg-body);
}
.auth-card {
  width: 380px;
  padding: 40px;
  background: var(--color-bg-card);
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
}
.auth-header {
  text-align: center;
  margin-bottom: 32px;
}
.auth-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 8px;
  letter-spacing: 2px;
}
.auth-subtitle {
  color: var(--color-text-muted);
  font-size: 14px;
  margin: 0;
}
.auth-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 13px;
  color: var(--color-text-muted);
}
</style>
