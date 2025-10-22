## Hackaton: RandomTrust - Прозрачный ГСЧ

### Setup
1. Copy `.env.example` to `.env` and fill secrets (DB pass, API URL).
2. `./setup_and_run.sh` — auto-install, DB setup, run (logs in *.log).
3. Local: http://localhost:5173
4. Server: http://31.129.108.187:5173 (set VITE_API_URL in .env).

### Git Push
- .env in .gitignore — secrets safe.
- For prod: Use PM2/systemd for nohup processes.

### Tech
- Backend: FastAPI + PostgreSQL + NIST.
- Frontend: SvelteKit + Chart.js.
- Env: Python 3, Node 18+.