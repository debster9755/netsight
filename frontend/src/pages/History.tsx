import { useEffect, useState } from 'react'
import { Clock, RefreshCw, CheckCircle, AlertTriangle, XCircle, Loader2 } from 'lucide-react'
import { api } from '../api/client'
import { useNavigate } from 'react-router-dom'

interface Run {
  id: string
  host: string
  created_at: string
  status: 'healthy' | 'warning' | 'critical'
}

export default function History() {
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/diagnostics/history').then(r => {
      setRuns(r.data)
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-accent" /></div>

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-sans font-bold text-white">Diagnostic History</h1>
        <p className="text-sm text-gray-500 mt-1">{runs.length} past runs</p>
      </div>

      {runs.length === 0 && (
        <div className="card text-center text-gray-500 py-12">
          <Clock size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">No diagnostics run yet. Start from the Diagnose page.</p>
        </div>
      )}

      <div className="space-y-2">
        {runs.map(run => {
          const Icon = run.status === 'healthy' ? CheckCircle : run.status === 'critical' ? XCircle : AlertTriangle
          const cls = run.status === 'healthy' ? 'text-success' : run.status === 'critical' ? 'text-danger' : 'text-warning'
          return (
            <div key={run.id} className="card flex items-center gap-4 hover:border-accent/40 transition-colors cursor-pointer" onClick={() => navigate(`/?host=${run.host}`)}>
              <Icon size={16} className={`${cls} shrink-0`} />
              <div className="flex-1">
                <p className="text-sm text-white font-sans">{run.host}</p>
                <p className="text-xs text-gray-500">{new Date(run.created_at).toLocaleString()}</p>
              </div>
              <span className={run.status === 'healthy' ? 'badge-ok' : run.status === 'critical' ? 'badge-err' : 'badge-warn'}>
                {run.status}
              </span>
              <button
                className="btn-ghost text-xs flex items-center gap-1"
                onClick={e => { e.stopPropagation(); navigate(`/?host=${run.host}`) }}
              >
                <RefreshCw size={12} /> Re-run
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
