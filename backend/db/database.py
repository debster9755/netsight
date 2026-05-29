import aiosqlite
from contextlib import asynccontextmanager
from backend.config import settings

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS diagnostic_runs (
    id          TEXT PRIMARY KEY,
    host        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    status      TEXT NOT NULL,
    results     TEXT,          -- JSON blob
    ai_analysis TEXT           -- JSON blob
);

CREATE TABLE IF NOT EXISTS capture_sessions (
    id          TEXT PRIMARY KEY,
    label       TEXT,
    created_at  TEXT NOT NULL,
    packets     INTEGER DEFAULT 0,
    summary     TEXT,          -- JSON blob
    ai_analysis TEXT
);

CREATE TABLE IF NOT EXISTS log_analyses (
    id          TEXT PRIMARY KEY,
    filename    TEXT,
    created_at  TEXT NOT NULL,
    format      TEXT,
    line_count  INTEGER,
    findings    TEXT,          -- JSON blob
    ai_analysis TEXT
);

CREATE TABLE IF NOT EXISTS resolution_playbook (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern     TEXT NOT NULL,
    description TEXT NOT NULL,
    commands    TEXT NOT NULL,  -- JSON array
    tags        TEXT            -- comma-separated
);
"""


@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db():
    async with aiosqlite.connect(settings.db_path) as db:
        await db.executescript(_CREATE_SQL)
        await db.commit()
        await _seed_playbook(db)


async def _seed_playbook(db: aiosqlite.Connection):
    count = await db.execute_fetchall("SELECT COUNT(*) AS c FROM resolution_playbook")
    if count[0]["c"] > 0:
        return
    entries = [
        ("dns_propagation", "DNS not propagated globally", '["dig +trace {host}", "nslookup {host} 8.8.8.8", "nslookup {host} 1.1.1.1"]', "dns"),
        ("ssl_expiry", "SSL certificate expired or expiring soon", '["openssl s_client -connect {host}:443", "curl -Iv https://{host}"]', "ssl,cdn"),
        ("cdn_cache_miss", "CDN cache miss rate too high — origin overloaded", '["curl -I https://{host} | grep -i x-cache", "curl -I https://{host}?nocache=1"]', "cdn,cache"),
        ("origin_5xx", "Origin returning 5xx errors", '["curl -v https://{host}/", "check origin server logs", "review CDN error log for upstream connect failures"]', "cdn,origin"),
        ("high_ttfb", "High TTFB — likely origin or network latency", '["mtr --report {host}", "traceroute {host}", "curl -w @curl-format.txt -o /dev/null -s https://{host}"]', "performance,latency"),
        ("tls_handshake_slow", "TLS handshake taking >500ms", '["openssl s_client -connect {host}:443 -debug", "check OCSP stapling config"]', "ssl,performance"),
    ]
    await db.executemany(
        "INSERT INTO resolution_playbook (pattern, description, commands, tags) VALUES (?, ?, ?, ?)",
        entries,
    )
    await db.commit()
