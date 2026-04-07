/**
 * SQL优化规则类型定义
 */

export type RuleSeverity = 'L0' | 'L1' | 'L2' | 'L3'
export type RuleCategory = 'index' | 'query' | 'schema' | 'performance' | 'security' | 'syntax'

export interface RuleResult {
  rule_name: string
  rule_id: string
  category: RuleCategory
  severity: RuleSeverity
  description: string
  suggestion: string
  sql_segment?: string
  fix_sql?: string
  metadata?: Record<string, any>
}

export interface AnalyzeRequest {
  sql: string
  explain_result?: any[]
  table_schema?: Record<string, any>
  indexes?: Record<string, any[]>
}

export interface AnalyzeResponse {
  suggestions: RuleResult[]
  total_issues: number
}

export interface RuleDetail {
  rule_id: string
  name: string
  description: string
  category: RuleCategory
  severity: RuleSeverity
  enabled: boolean
}
