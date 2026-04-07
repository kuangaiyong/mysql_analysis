const BASE_URL = import.meta.env.VITE_BASE_API || 'http://localhost:8088/api/v1'
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8088/ws'

export const config = {
  baseApi: BASE_URL,
  wsUrl: WS_URL,
  title: 'MySQL性能诊断与优化系统'
}
