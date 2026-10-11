#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$TASK_ROOT"
node --input-type=module <<'JS'
const raw = process.env.VITE_API_BASE_URL;
let valid = false;
try {
  const url = new URL(raw);
  valid = url.protocol === 'https:' && !url.username && !url.password &&
    url.pathname === '/' && !url.search && !url.hash &&
    !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
} catch {}
if (!valid) {
  console.error('Set VITE_API_BASE_URL to the public HTTPS backend origin before building.');
  process.exit(1);
}
JS
printf 'Building EventOps release %s\n' "${RENDER_GIT_COMMIT:-ci-or-local}"
npm --prefix frontend ci
npm --prefix frontend run build
