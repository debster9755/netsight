import { Sparkles, Terminal, ArrowRight } from 'lucide-react'
import { AiAnalysis } from '../api/client'

export default function AIPanel({ analysis }: { analysis: AiAnalysis }) {
  const conf = Math.round((analysis.confidence || 0) * 100)
  const sev = analysis.severity || 'unknown'
  const sevClass = { healthy: 'badge-ok', warning: 'badge-warn', critical: 'badge-err', unknown: 'badge-info' }[sev] || 'badge-info'

  return (
    <div className="card border-indigo-500/30 space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles size={16} className="text-accent" />
        <span className="font-sans font-semibold text-white text-sm">AI Analysis</span>
        <span className={sevClass}>{sev}</span>
        <span className="text-xs text-gray-600 ml-auto">{conf}% confidence</span>
      </div>

      <div>
        <p className="text-sm text-gray-300 font-sans">{analysis.root_cause}</p>
      </div>

      {analysis.findings?.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5">Findings</p>
          <ul className="space-y-1">
            {analysis.findings.map((f, i) => (
              <li key={i} className="text-sm text-gray-400 flex gap-2">
                <span className="text-warning shrink-0">·</span>{f}
              </li>
            ))}
          </ul>
        </div>
      )}

      {analysis.recommended_commands?.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <Terminal size={11} /> Recommended Commands
          </p>
          <div className="space-y-1">
            {analysis.recommended_commands.map((cmd, i) => (
              <code key={i} className="block text-xs bg-surface px-3 py-1.5 rounded text-accent-hover">{cmd}</code>
            ))}
          </div>
        </div>
      )}

      {analysis.resolution_steps?.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5">Resolution Steps</p>
          <ol className="space-y-1">
            {analysis.resolution_steps.map((s, i) => (
              <li key={i} className="text-sm text-gray-400 flex gap-2">
                <span className="text-accent shrink-0">{i + 1}.</span>{s}
              </li>
            ))}
          </ol>
        </div>
      )}

      {analysis.escalation_path && (
        <div className="flex gap-2 items-start text-sm text-gray-500 border-t border-border pt-3">
          <ArrowRight size={14} className="shrink-0 mt-0.5 text-gray-600" />
          <span><strong className="text-gray-400">Escalation:</strong> {analysis.escalation_path}</span>
        </div>
      )}
    </div>
  )
}
