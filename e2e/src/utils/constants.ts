export const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  connections: '/api/v1/connections',
  monitoring: '/api/v1/monitoring',
  slowQueries: '/api/v1/slow-queries',
  explain: '/api/v1/explain',
  indexes: '/api/v1/connections',
  tables: '/api/v1/table',
  alerts: '/api/v1/alerts',
  reports: '/api/v1/reports'
} as const;

export const PAGE_PATHS = {
  dashboard: '/',
  connections: '/connections',
  monitoring: '/monitoring',
  slowQuery: '/slow-query',
  explain: '/explain',
  indexManagement: '/index-management',
  tableStructure: '/table-structure',
  alerts: '/alerts',
  alertHistory: '/alerts/history',
  reports: '/reports'
} as const;

export const SELECTORS = {
  page: {
    title: '.page-title',
    loading: '.el-loading-mask',
    errorMessage: '.el-message--error',
    successMessage: '.el-message--success'
  },
  connection: {
    addButton: 'button:has-text("添加连接")',
    table: '.el-table',
    nameInput: 'input[placeholder="请输入连接名称"]',
    hostInput: 'input[placeholder="请输入主机地址"]',
    saveButton: 'button:has-text("保存")',
    testButton: 'button:has-text("测试连接")'
  },
  monitoring: {
    startButton: 'button:has-text("启动监控")',
    stopButton: 'button:has-text("停止监控")',
    chartContainer: '.chart-container'
  },
  slowQuery: {
    table: '.slow-query-table',
    analyzeButton: 'button:has-text("分析")',
    optimizeButton: 'button:has-text("优化建议")'
  },
  explain: {
    sqlInput: 'textarea[placeholder*="请输入SQL语句"]',
    analyzeButton: 'button:has-text("分析")',
    resultContainer: '.explain-result'
  }
} as const;
