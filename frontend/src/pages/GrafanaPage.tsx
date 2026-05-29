import { useEffect, useState } from 'react'
import { BarChart2, AlertCircle, CheckCircle, Clock, Loader2 } from 'lucide-react'
import { api, GrafanaAlert } from '../api/client'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts'

export default function GrafanaPage() {
  const [alerts, setAlerts] = useState<GrafanaAlert[]>([])
  const [metrics, setMetrics] = useState<any>(null)
  const [mode, setMode] = useState<string>('mock')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      const [alertRes, metricRes, statusRes] = await Promise.all([
        api.get('/grafana/alerts'),
        api.get('/grafana/metrics?window=60'),
        api.get('/grafana/status'),
      ])
      setAlerts(alertRes.data)
      setMetrics(metricRes.data)
      setMode(statusRes.data.mode)
      setLoading(false)
    }
    load()
  }, [])

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-accent" /></div>

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-sans font-bold text-white">Grafana Metrics</h1>
          <p className="text-sm text-gray-500 mt-1">CDN health metrics · Active alerts · Incident correlation</p>
        </div>
        <span className={mode === 'real' ? 'badge-ok' : 'badge-info'}>{mode === 'real' ? 'Live Grafana' : 'Mock data'}</span>
      </div>

      {/* Alerts */}
      <div className="card space-y-3">
        <p className="font-sans font-medium text-white text-sm">Active Alerts</p>
        {alerts.map((a) => {
          const Icon = a.state === 'ok' ? CheckCircle : a.state === 'alerting' ? AlertCircle : Clock
          const cls = a.state === 'ok' ? 'text-success' : a.state === 'alerting' ? 'text-danger' : 'text-warning'
          return (
            <div key={a.id} className="flex items-start gap-3 py-2 border-b border-border last:border-0">
              <Icon size={16} className={`${cls} shrink-0 mt-0.5`} />
              <div className="flex-1">
                <p className="text-sm font-sans text-white">{a.name}</p>
                <p className="text-xs text-gray-500">{a.message}</p>
              </div>
              <span className={a.severity === 'critical' ? 'badge-err' : a.severity === 'warning' ? 'badge-warn' : 'badge-info'}>
                {a.severity}
              </span>
            </div>
          )
        })}
      </div>

      {/* Metric charts */}
      {metrics?.series && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricChart
            label="P95 Latency (ms)"
            data={metrics.series.latency_ms?.data || []}
            incident={metrics.incident_window}
            color="#6366f1"
          />
          <MetricChart
            label="Error Rate (%)"
            data={metrics.series.error_rate_pct?.data || []}
            incident={metrics.incident_window}
            color="#ef4444"
          />
          <MetricChart
            label="Cache Hit Ratio (%)"
            data={metrics.series.cache_hit_pct?.data || []}
            incident={metrics.incident_window}
            color="#22c55e"
          />
          <MetricChart
            label="Requests/s"
            data={metrics.series.req_per_sec?.data || []}
            incident={metrics.incident_window}
            color="#f59e0b"
          />
        </div>
      )}
    </div>
  )
}

function MetricChart({ label, data, incident, color }: { label: string; data: [number, number][]; incident: any; color: string }) {
  const chartData = data.map(([ts, v]) => ({
    time: new Date(ts * 1000).toISOString().slice(11, 16),
    value: v,
  }))

  return (
    <div className="card">
      <p className="text-sm font-sans text-gray-400 mb-3">{label}</p>
      <ResponsiveContainer width="100%" height={140}>
        <LineChart data={chartData} margin={{ top: 0, right: 4, bottom: 0, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
          <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#6b7280' }} interval={9} />
          <YAxis tick={{ fontSize: 9, fill: '#6b7280' }} />
          <Tooltip contentStyle={{ background: '#1a1d27', border: '1px solid #2a2d3a', fontSize: 11 }} />
          <Line type="monotone" dataKey="value" stroke={color} dot={false} strokeWidth={1.5} />
          {incident && (
            <ReferenceLine x={new Date(incident.start * 1000).toISOString().slice(11, 16)} stroke="#ef4444" strokeDasharray="4 2" label={{ value: 'Incident', fontSize: 9, fill: '#ef4444' }} />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
