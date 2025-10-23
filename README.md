## RandomTrust: Прозрачный ГСЧ

### Модули
- **Backend**: models.py (DB), database.py (engine), generators.py (seq), nist_service.py (тесты), analyze.py (upload).
- **Frontend**: components/ (Upload.svelte, Analysis.svelte), services/api.ts (fetch).

### Upload-модуль
1. TXT/CSV: Числа 0-99 по строкам.
2. POST /analyze — парсит, entropy/NIST, сравнение с эталоном (secrets PRNG).
3. UI: Загрузка + таблица (user vs ref).

### Setup
- cp .env.example .env; edit pass/IP.
- ./setup_and_run.sh.
- Test: Upload sample.txt (nums), see analysis.

### Демо
- Генерация: /generate/chaotic.
- Upload: Frontend file input → таблица NIST/compare.