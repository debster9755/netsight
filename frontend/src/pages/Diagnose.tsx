import { useState } from 'react'
import { Search, Loader2, AlertTriangle, CheckCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { api, DiagnosticResult, AiAnalysis } from '../api/client'
import AIPanel from '../components/AIPanel'

export default function Diagnose() {
  const [host, setHost] = useState('')
  const [runAi, setRunAi] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<DiagnosticResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    if (!host.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const { data } = await api.post('/diagnostics/', { host: host.trim(), run_ai: runAi })
      setResult(data)
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-sans font-bold text-white">Network Diagnostic</h1>
        <p className="text-sm text-gray-500 mt-1">DNS · SSL · HTTP probe · Traceroute · MTR — all in parallel</p>
      </div>

      {/* Input */}
      <div className="card flex gap-3 items-center">
        <input
          className="input flex-1"
          placeholder="bunny.net or https://bunny.net/storage"
          value={host}
          onChange={e => setHost(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && run()}
        />
        <label className="flex items-center gap-2 text-sm text-gray-400 font-sans whitespace-nowrap">
          <input type="checkbox" checked={runAi} onChange={e => setRunAi(e.target.checked)} className="accent-indigo-500" />
          AI analysis
        </label>
        <button onClick={run} disabled={loading} className="btn-primary flex items-center gap-2">
          {loading ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}
          Run
        </button>
      </div>

      {error && (
        <div className="card border-danger/40 text-danger text-sm flex gap-2 items-start">
          <XCircle size={16} className="shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          {/* Status banner */}
          <StatusBanner result={result} />

          {/* Result cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <DiagCard title="DNS" data={result.dns} />
            <DiagCard title="SSL / TLS" data={result.ssl} />
            <DiagCard title="HTTP" data={result.http} />
            <DiagCard title="Traceroute" data={result.traceroute} />
          </div>

          {result.ai_analysis && <AIPanel analysis={result.ai_analysis as AiAnalysis} />}
        </div>
      )}
    </div>
  )
}

function StatusBanner({ result }: { result: DiagnosticResult }) {
  const color = { healthy: 'success', warning: 'warning', critical: 'danger' }[result.status] || 'info'
  const Icon = result.status === 'healthy' ? CheckCircle : result.status === 'critical' ? XCircle : AlertTriangle
  return (
    <div className={`card border-${color}/30 flex items-start gap-3`}>
      <Icon size={18} className={`text-${color} shrink-0 mt-0.5`} />
      <div>
        <p className={`font-sans font-semibold text-${color} capitalize`}>{result.status}</p>
        <ul className="mt-1 space-y-0.5">
          {result.summary.map((s, i) => <li key={i} className="text-sm text-gray-400">{s}</li>)}
        </ul>
      </div>
    </div>
  )
}

function DiagCard({ title, data }: { title: string; data: Record<string, unknown> }) {
  const [open, setOpen] = useState(false)
  const ok = data?.ok !== false
  return (
    <div className="card space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-sans font-medium text-white text-sm">{title}</span>
          <span className={ok ? 'badge-ok' : 'badge-err'}>{ok ? 'OK' : 'FAIL'}</span>
        </div>
        <button onClick={() => setOpen(!open)} className="text-gray-600 hover:text-white">
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>
      <DiagSummary title={title} data={data} />
      {open && (
        <pre className="text-xs text-gray-500 overflow-auto max-h-64 bg-surface rounded p-2 mt-2">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  )
}

function DiagSummary({ title, data }: { title: string; data: Record<string, unknown> }) {
  if (title === 'DNS') {
    const addrs = (data.primary_addresses as string[]) || []
    return <p className="text-sm text-gray-400">{addrs.join(', ') || 'No result'} {data.cdn_hint ? `· ${data.cdn_hint}` : ''}</p>
  }
  if (title === 'SSL / TLS') {
    if (!data.ok) return <p className="text-sm text-danger">{data.error as string}</p>
    return <p className="text-sm text-gray-400">{data.tls_version as string} · {data.days_remaining as number}d remaining · {data.issuer_org as string}</p>
  }
  if (title === 'HTTP') {
    if (!data.ok) return <p className="text-sm text-danger">{data.error as string}</p>
    const t = (data.timings_ms as Record<string, number>) || {}
    return <p className="text-sm text-gray-400">HTTP {data.status_code as number} · TTFB {t.ttfb}ms · {(data.cdn as string) || 'no CDN'}</p>
  }
  if (title === 'Traceroute') {
    const hops = data.hop_count as number
    const max = data.max_rtt_ms as number
    const anomalies = (data.anomalies as string[]) || []
    return <p className="text-sm text-gray-400">{hops} hops · max {max}ms {anomalies.length ? `· ⚠ ${anomalies.length} anomaly` : ''}</p>
  }
  return null
}
