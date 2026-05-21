import { ref } from 'vue'
import { useMessage } from 'naive-ui'

/**
 * Composable — SSE 生成状态机。
 *
 * 封装 3 套重复的生成流程（世界观/地图/人物）为一个统一的组合式函数。
 *
 * @param {Object} options
 * @param {string} options.genType  生成类型标识，用于提示文本
 * @param {number} options.bookId   book ID
 * @param {Function} options.fetchInjectionsFn  (bookId) => Promise<{items:[]}>
 * @param {Function} options.generateFn         (bookId, handlers, body) => AbortController
 * @param {Function} options.onReload           关闭后调用的刷新回调
 */
export function useSSEGeneration({ genType, bookId, fetchInjectionsFn, generateFn, onReload }) {
  const message = useMessage()

  const visible = ref(false)
  const output = ref('')
  const model = ref('')
  const tokens = ref(0)
  const running = ref(false)
  const phase = ref('idle') // 'idle' | 'generating' | 'done'
  const abort = ref(null)
  const injectionItems = ref([])
  const result = ref(null)

  const successMessages = {
    worldview: '世界观设定生成完成',
    map: '地图设定生成完成',
    character: '人物生成完成',
  }

  async function prepare() {
    output.value = ''
    model.value = ''
    tokens.value = 0
    running.value = false
    phase.value = 'idle'
    injectionItems.value = []
    result.value = null
    visible.value = true
    try {
      const data = await fetchInjectionsFn(bookId.value)
      injectionItems.value = data.items || []
    } catch (e) {
      console.error(`Failed to fetch ${genType} injection items:`, e)
    }
  }

  function start(overrides, userPrompt) {
    phase.value = 'generating'
    running.value = true

    const body = { user_prompt: userPrompt || '' }
    if (overrides && (overrides.exclude_variables?.length || overrides.extra_variables || overrides.added_character_ids?.length)) {
      body.injection_overrides = overrides
    }

    abort.value = generateFn(bookId.value, {
      onStart: (evt) => {
        model.value = evt.model || ''
        tokens.value = evt.token_estimate || 0
      },
      onToken: (token) => {
        output.value += token
      },
      onSummary: (summary) => {
        result.value = summary
      },
      onDone: () => {
        running.value = false
        phase.value = 'done'
        if (genType !== 'character') {
          message.success(successMessages[genType] || '生成完成')
        }
      },
      onError: (err) => {
        running.value = false
        phase.value = 'done'
        message.error(err)
      },
    }, body)
  }

  function cancel() {
    abort.value?.abort()
    running.value = false
    phase.value = 'idle'
    message.info('已取消生成')
  }

  function close() {
    visible.value = false
    if (onReload) onReload()
  }

  return {
    visible, output, model, tokens, running, phase, injectionItems, result,
    prepare, start, cancel, close,
  }
}
