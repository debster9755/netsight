import { Routes, Route, NavLink } from 'react-router-dom'
import { Activity, Radio, FileText, BarChart2, Clock, Telescope } from 'lucide-react'
import Diagnose from './pages/Diagnose'
import Capture from './pages/Capture'
import LogAnalysis from './pages/LogAnalysis'
import GrafanaPage from './pages/GrafanaPage'
import History from './pages/History'

const NAV = [
  { to: '/', icon: Activity, label: 'Diagnose' },
  { to: '/capture', icon: Radio, label: 'Capture' },
  { to: '/logs', icon: FileText, label: 'Logs' },
  { to: '/grafana', icon: BarChart2, label: 'Grafana' },
  { to: '/history', icon: Clock, label: 'History' },
]

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-52 bg-panel border-r border-border flex flex-col shrink-0">
        <div className="px-4 py-5 border-b border-border flex items-center gap-2">
          <Telescope size={20} className="text-accent" />
          <span className="font-sans font-bold text-white tracking-wide">NetSight</span>
        </div>
        <nav className="flex-1 py-3 space-y-0.5 px-2">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-sans transition-colors ${
                  isActive
                    ? 'bg-accent/20 text-accent-hover'
                    : 'text-gray-400 hover:text-white hover:bg-border/50'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-3 border-t border-border text-xs text-gray-600">v0.1.0 MVP</div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto bg-surface">
        <Routes>
          <Route path="/" element={<Diagnose />} />
          <Route path="/capture" element={<Capture />} />
          <Route path="/logs" element={<LogAnalysis />} />
          <Route path="/grafana" element={<GrafanaPage />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </main>
    </div>
  )
}
