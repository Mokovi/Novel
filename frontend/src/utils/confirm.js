/**
 * Promise-based confirm dialog using Naive UI discrete API.
 * Can be used outside of Vue setup() context.
 */
import { createDiscreteApi } from 'naive-ui'

export function showConfirm(options) {
  const { dialog } = createDiscreteApi(['dialog'])

  return new Promise((resolve) => {
    dialog.warning({
      title: options.title || '确认',
      content: options.content || '确定执行此操作吗？',
      positiveText: options.positiveText || '确定',
      negativeText: options.negativeText || '取消',
      onPositiveClick: () => {
        resolve(true)
      },
      onNegativeClick: () => {
        resolve(false)
      },
      onClose: () => {
        resolve(false)
      },
      ...options,
    })
  })
}
