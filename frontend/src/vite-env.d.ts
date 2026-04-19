/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BASE_API: string
  readonly VITE_WS_URL: string
  readonly VITE_APP_TITLE: string
  readonly MODE: string
  readonly DEV: boolean
  readonly PROD: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module 'element-plus/dist/locale/zh-cn.js' {
  import type { Language } from 'element-plus/es/locale'

  const locale: Language
  export default locale
}
