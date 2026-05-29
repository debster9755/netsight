# NetSight 🔭

> **Intelligent Network Diagnostic & Observability Platform**  
> Wireshark + Fiddler + Grafana + AI SRE — in one browser tab.

Built for CDN/edge infrastructure support engineers. Replaces the scattered toolkit of `traceroute`, `curl`, `mtr`, `dig`, Wireshark, tcpdump, and Fiddler with a unified web app that adds AI-powered root cause analysis and resolution recommendations.

---

## Features

| Feature | Description |
|---|---|
| **Unified Diagnostics** | DNS · SSL/TLS · HTTP timing · Traceroute · MTR — all in parallel |
| **Live Packet Capture** | Real-time scapy capture streamed to browser (requires root) |
| **File Analysis** | Upload HAR or PCAP — get waterfall + AI session summary |
| **Log Triage** | nginx · CDN · syslog — auto-detect + error spike analysis |
| **Grafana Integration** | Mock metrics for MVP, real Grafana API via env toggle |
| **AI Analysis** | Claude-powered root cause + confidence + resolution steps |

---

## Quick Start

### Option 1 — Local (recommended for development)

**Prerequisites:** Python 3.11+, Node 20+, `traceroute` installed

```bash
git clone <your-repo>
cd netsight

# Backend
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Option 2 — Docker Compose

```bash
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY
docker compose up --build
# → http://localhost:5173
```

> **Live capture note:** Requires running the backend as root (or with `CAP_NET_RAW`). Without root, file-based analysis works fully.

---

## Configuration

Copy `.env.example` to `.env` and fill in:

```env
ANTHROPIC_API_KEY=sk-ant-...      # Required for AI analysis

GRAFANA_URL=                       # Optional: your Grafana instance
GRAFANA_API_TOKEN=                 # Optional: Grafana API token

CAPTURE_INTERFACE=en0              # Network interface for live capture
```

Without `GRAFANA_URL`, the app uses realistic mock CDN metrics for demo.

---

## API Reference

| Endpoint | Description |
|---|---|
| `POST /diagnostics/` | Run full diagnostic suite on a host |
| `GET /diagnostics/history` | Past diagnostic runs |
| `WS /capture/live` | Live packet stream |
| `POST /capture/upload` | Upload HAR or PCAP file |
| `POST /logs/analyze` | Analyze log file |
| `GET /grafana/alerts` | Active alerts (mock or real) |
| `GET /grafana/metrics` | CDN time-series metrics |
| `POST /ai/analyze` | Run AI analysis on arbitrary data |
| `GET /ai/playbook` | Resolution playbook (common CDN issues) |

Full interactive docs: `http://localhost:8000/docs`

---

## Example Files

The `examples/` folder contains:
- `sample.log` — nginx access log with simulated errors and slow requests
- `sample.har` — browser HAR file with a slow API call and a 404

---

## Architecture

```
backend/
├── core/diagnostics/    # traceroute, DNS, SSL, HTTP, MTR
├── core/capture/        # scapy live, PCAP parser, HAR parser
├── core/logs/           # nginx/CDN/syslog parsers + analyzer
├── core/grafana/        # real API client + mock data
├── ai/                  # Claude API + prompt caching
├── db/                  # SQLite + aiosqlite
└── routers/             # FastAPI route handlers

frontend/
└── src/
    ├── pages/           # Diagnose, Capture, Logs, Grafana, History
    ├── components/      # AIPanel, DiagCard, Waterfall, PacketTable
    └── api/             # Axios client + type definitions
```

---

## Stack

- **Backend:** Python 3.11 · FastAPI · Uvicorn · aiosqlite
- **Diagnostics:** httpx · dnspython · pyOpenSSL · icmplib
- **Capture:** scapy · dpkt · haralyzer
- **AI:** Anthropic Claude API (`claude-sonnet-4-6`) + prompt caching
- **Frontend:** React 18 · Vite · Tailwind CSS · Recharts
- **Deploy:** Docker Compose

---

## Roadmap

- [ ] MCP server — expose NetSight as Claude Code tools
- [ ] PDF/JSON export for diagnostic reports
- [ ] Webhook alerts (Slack/PagerDuty) on critical findings
- [ ] Multi-hop CDN path visualization
- [ ] Real-time Grafana alert webhook ingestion

---

*Built as part of an AI Pet Project Portfolio — 2026*
