import { ElNotification } from 'element-plus'

function notify(msg, type) {
  if (!type) {
    const message = msg || ''
    const isError = /失败|错误|无效|不存在|不能|已被|请先|请检查|请填写|不足|未登录|已过期/.test(message)
    const isWarning = /为空|不一致/.test(message)
    type = isError ? 'error' : isWarning ? 'warning' : 'success'
  }
  const title = type === 'error' ? '操作失败' : type === 'warning' ? '提示' : '操作成功'
  ElNotification({ title, message: msg || '', type, duration: 3000 })
}

export function useToast() {
  return { show: notify }
}
