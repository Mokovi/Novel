<template>
  <n-form :model="form" :rules="rules" ref="formRef" label-placement="top" size="small">
    <n-form-item label="姓名" path="name">
      <n-input v-model:value="form.name" placeholder="输入人物姓名" />
    </n-form-item>
    <n-form-item label="别名" path="aliases">
      <n-input v-model:value="form.aliases" placeholder="多个别名用逗号分隔" />
    </n-form-item>
    <n-form-item label="角色类型" path="role_type">
      <n-select
        v-model:value="form.role_type"
        :options="roleOptions"
        placeholder="选择角色类型"
        clearable
      />
    </n-form-item>
    <n-form-item label="状态" path="status">
      <n-select v-model:value="form.status" :options="statusOptions" />
    </n-form-item>
    <n-form-item label="描述" path="description">
      <n-input v-model:value="form.description" type="textarea" :rows="3" placeholder="简要描述人物" />
    </n-form-item>
    <n-form-item label="外貌" path="appearance">
      <n-input v-model:value="form.appearance" type="textarea" :rows="3" placeholder="外貌特征" />
    </n-form-item>
    <n-form-item label="性格" path="personality">
      <n-input v-model:value="form.personality" type="textarea" :rows="3" placeholder="性格特点" />
    </n-form-item>
    <n-form-item label="背景" path="background">
      <n-input v-model:value="form.background" type="textarea" :rows="4" placeholder="身世背景" />
    </n-form-item>
    <n-form-item label="目标" path="goals">
      <n-input v-model:value="form.goals" type="textarea" :rows="3" placeholder="动机与目标" />
    </n-form-item>
    <div class="form-actions">
      <n-button @click="$emit('cancel')">取消</n-button>
      <n-button type="primary" :loading="saving" @click="handleSubmit">保存</n-button>
    </div>
  </n-form>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useMessage } from 'naive-ui'
import { createCharacter, updateCharacter } from '../../api/characters.js'

const props = defineProps({
  character: { type: Object, default: null },
  bookId: { type: Number, required: true },
})
const emit = defineEmits(['saved', 'cancel'])

const message = useMessage()
const formRef = ref(null)
const saving = ref(false)

const roleOptions = [
  { label: '主角', value: 'protagonist' },
  { label: '反派', value: 'antagonist' },
  { label: '配角', value: 'supporting' },
  { label: '龙套', value: 'minor' },
]

const statusOptions = [
  { label: '活跃', value: 'active' },
  { label: '已故', value: 'deceased' },
  { label: '失踪', value: 'missing' },
  { label: '其他', value: 'other' },
]

const rules = {
  name: { required: true, message: '请输入人物姓名', trigger: 'blur' },
}

const form = ref({
  name: '',
  aliases: '',
  role_type: null,
  status: 'active',
  description: '',
  appearance: '',
  personality: '',
  background: '',
  goals: '',
})

onMounted(() => {
  if (props.character) {
    form.value = { ...props.character }
  }
})

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    if (props.character?.id) {
      await updateCharacter(props.character.id, form.value)
      message.success('人物已更新')
    } else {
      await createCharacter(form.value, props.bookId)
      message.success('人物已创建')
    }
    emit('saved')
  } catch (e) {
    message.error(e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
</style>
