import { useState } from 'react'
import { FileText, Upload, Loader2, AlertTriangle } from 'lucide-react'
import { api } from '../api/client'
import AIPanel from '../components/AIPanel'

export default function LogAnalysis() {
  const [result, setResult] = useState<any>(null)
  const [uploading, setUploading] = useState(false)
  const [runAi, setRunAi] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async (file: File) => {
    setUploading(true)
    setResult(null)
    setError(null)
    const form = new FormData()
    form.append('file', file)
    form.append('run_ai', String(runAi))
    try {
      const { data } = await api.post('/logs/analyze', form)
      setResult(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-sans font-bold text-white">Log Triage</h1>
        <p className="text-sm text-gray-500 mt-1">Auto-detect nginx · CDN · syslog — find error spikes, slow paths, abuse</p>
      </div>

      <div
        className="card border-dashed flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-accent transition-colors min-h-[180px]"
        onDragOver={e => e.preventDefault()}
        onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleUpload(f) }}
        onClick={() => document.getElementById('logInput')?.click()}
      >
        {uploading ? <Loader2 size={28} className="text-accent animate-spin" /> : <FileText size={28} className="text-gray-500" />}
        <p className="text-sm text-gray-400">Drop log file here (nginx, CDN, syslog)</p>
        <label className="flex items-center gap-2 text-xs text-gray-500" onClick={e => e.stopPropagation()}>
          <input type="checkbox" checked={runAi} onChange={e => setRunAi(e.target.checked)} className="accent-indigo-500" />
          Include AI root cause analysis
        </label>
        <input id="logInput" type="file" accept=".log,.txt,.gz" hidden onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f) }} />
      </div>

      {error && <p className="text-danger text-sm">{error}</p>}

      {result && (
        <div className="space-y-4">
          {/* Stats */}
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <p className="font-sans font-medium text-white text-sm">{result.filename}</p>
              <span className="badge-info">{result.format}</span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <Stat label="Lines" value={result.line_count} />
              <Stat label="Parsed" value={result.parsed_count} />
              <Stat label="Findings" value={result.findings?.length || 0} />
            </div>
          </div>

          {/* Findings */}
          {result.findings?.length > 0 && (
            <div className="card space-y-2">
              <p className="text-xs text-gray-500 uppercase tracking-wider">Findings</p>
              {result.findings.map((f: string, i: number) => (
                <div key={i} className="flex gap-2 text-sm items-start">
                  <AlertTriangle size={14} className="text-warning shrink-0 mt-0.5" />
                  <span className="text-gray-300">{f}</span>
                </div>
              ))}
            </div>
          )}

          {/* Stats breakdown */}
          {result.stats && (
            <div className="card">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Statistics</p>
              <pre className="text-xs text-gray-400 overflow-auto max-h-48">
                {JSON.stringify(result.stats, null, 2)}
              </pre>
            </div>
          )}

          {result.ai_analysis && <AIPanel analysis={result.ai_analysis} />}
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-mono text-white">{value}</p>
    </div>
  )
}
