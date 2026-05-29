import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export const WS_BASE = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api`

export interface DiagnosticResult {
  id: string
  host: string
  url: string
  created_at: string
  status: 'healthy' | 'warning' | 'critical'
  dns: Record<string, unknown>
  ssl: Record<string, unknown>
  http: Record<string, unknown>
  traceroute: Record<string, unknown>
  mtr: Record<string, unknown> | null
  summary: string[]
  ai_analysis?: AiAnalysis
}

export interface AiAnalysis {
  root_cause: string
  confidence: number
  severity: string
  findings: string[]
  recommended_commands: string[]
  escalation_path: string
  resolution_steps: string[]
}

export interface GrafanaAlert {
  id: number | string
  name: string
  state: 'ok' | 'alerting' | 'pending'
  severity: string
  message: string
  panel: string
  dashboard: string
  fired_at: string | null
}
