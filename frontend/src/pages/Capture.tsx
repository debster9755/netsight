import { useState, useRef, useCallback } from 'react'
import { Radio, Upload, Loader2, Wifi, WifiOff } from 'lucide-react'
import { api, WS_BASE } from '../api/client'
import AIPanel from '../components/AIPanel'

interface Packet {
  ts?: number
  src?: string
  dst?: string
  proto?: string
  sport?: number
  dport?: number
  len?: number
  payload_hint?: string
  keepalive?: boolean
  error?: string
  captured?: number
}

export default function Capture() {
  const [packets, setPackets] = useState<Packet[]>([])
  const [capturing, setCapturing] = useState(false)
  const [liveError, setLiveError] = useState<string | null>(null)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [uploading, setUploading] = useState(false)
  const [runAi, setRunAi] = useState(false)
  const [hostFilter, setHostFilter] = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  const startCapture = useCallback(() => {
    setPackets([])
    setLiveError(null)
    setCapturing(true)
    const params = new URLSearchParams({ max_packets: '300' })
    if (hostFilter) params.set('host_filter', hostFilter)
    const ws = new WebSocket(`${WS_BASE}/capture/live?${params}`)
    wsRef.current = ws
    ws.onmessage = (e) => {
      const pkt: Packet = JSON.parse(e.data)
      if (pkt.error) { setLiveError(pkt.error); ws.close(); return }
      if (pkt.keepalive) return
      setPackets(prev => [pkt, ...prev].slice(0, 500))
    }
    ws.onclose = () => setCapturing(false)
    ws.onerror = () => { setLiveError('WebSocket error'); setCapturing(false) }
  }, [hostFilter])

  const stopCapture = () => wsRef.current?.close()

  const handleUpload = async (file: File) => {
    setUploading(true)
    setUploadResult(null)
    const form = new FormData()
    form.append('file', file)
    form.append('run_ai', String(runAi))
    try {
      const { data } = await api.post('/capture/upload', form)
      setUploadResult(data)
    } catch (e: any) {
      setUploadResult({ ok: false, error: e.message })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-sans font-bold text-white">Packet Capture</h1>
        <p className="text-sm text-gray-500 mt-1">Live capture (requires root) · Upload HAR or PCAP file</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Live capture */}
        <div className="card space-y-3">
          <div className="flex items-center gap-2">
            {capturing ? <Wifi size={16} className="text-success animate-pulse" /> : <WifiOff size={16} className="text-gray-500" />}
            <span className="font-sans font-semibold text-white text-sm">Live Capture</span>
          </div>
          <input className="input" placeholder="Host filter (optional, e.g. 8.8.8.8)" value={hostFilter} onChange={e => setHostFilter(e.target.value)} />
          {liveError && <p className="text-danger text-xs">{liveError}</p>}
          <div className="flex gap-2">
            <button onClick={startCapture} disabled={capturing} className="btn-primary">Start</button>
            <button onClick={stopCapture} disabled={!capturing} className="btn-ghost">Stop</button>
          </div>
          <p className="text-xs text-gray-600">{packets.length} packets captured</p>
        </div>

        {/* File upload */}
        <div
          className="card border-dashed flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-accent transition-colors min-h-[140px]"
          onDragOver={e => { e.preventDefault() }}
          onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleUpload(f) }}
          onClick={() => document.getElementById('fileInput')?.click()}
        >
          {uploading ? <Loader2 size={24} className="text-accent animate-spin" /> : <Upload size={24} className="text-gray-500" />}
          <p className="text-sm text-gray-400">Drop HAR or PCAP file here</p>
          <label className="flex items-center gap-2 text-xs text-gray-500" onClick={e => e.stopPropagation()}>
            <input type="checkbox" checked={runAi} onChange={e => setRunAi(e.target.checked)} className="accent-indigo-500" />
            Include AI analysis
          </label>
          <input id="fileInput" type="file" accept=".har,.pcap,.pcapng,.cap" hidden onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f) }} />
        </div>
      </div>

      {/* Packet table */}
      {packets.length > 0 && (
        <div className="card overflow-auto max-h-72">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-500 text-left border-b border-border">
                <th className="pb-2 pr-4">Time</th>
                <th className="pb-2 pr-4">Src</th>
                <th className="pb-2 pr-4">Dst</th>
                <th className="pb-2 pr-4">Proto</th>
                <th className="pb-2 pr-4">Len</th>
                <th className="pb-2">Payload</th>
              </tr>
            </thead>
            <tbody>
              {packets.map((p, i) => (
                <tr key={i} className="border-b border-border/40 hover:bg-panel/50">
                  <td className="py-1 pr-4 text-gray-600">{p.ts ? new Date(p.ts * 1000).toISOString().slice(11, 23) : '-'}</td>
                  <td className="pr-4 text-gray-300">{p.src}:{p.sport}</td>
                  <td className="pr-4 text-gray-300">{p.dst}:{p.dport}</td>
                  <td className="pr-4"><span className="badge-info">{p.proto}</span></td>
                  <td className="pr-4 text-gray-500">{p.len}B</td>
                  <td className="text-gray-600 truncate max-w-xs">{p.payload_hint || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Upload result */}
      {uploadResult && (
        <div className="space-y-4">
          <div className="card">
            <p className="font-sans font-medium text-white text-sm mb-2">Analysis Result</p>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <Stat label="Requests" value={uploadResult.entry_count || uploadResult.http_request_count || 0} />
              <Stat label="Anomalies" value={(uploadResult.anomalies || []).length} />
              <Stat label="Total Size" value={uploadResult.total_size_kb ? `${uploadResult.total_size_kb}KB` : '-'} />
            </div>
            {uploadResult.anomalies?.length > 0 && (
              <ul className="mt-3 space-y-1">
                {uploadResult.anomalies.slice(0, 10).map((a: string, i: number) => (
                  <li key={i} className="text-xs text-warning flex gap-2"><span>·</span>{a}</li>
                ))}
              </ul>
            )}
          </div>
          {uploadResult.ai_analysis && <AIPanel analysis={uploadResult.ai_analysis} />}
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
