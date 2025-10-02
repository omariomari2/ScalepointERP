## Technical README (tech.md)

### Purpose
This document describes the technical architecture, stack choices, deployment model, and key trade‑offs of the ERP system. It complements the high‑level `README.md` by focusing purely on how the system is built and operated.

### Tech Stack Overview
- **Runtime**: Python 3.9
- **Web Framework**: Flask (factory pattern)
- **ORM**: SQLAlchemy 2.x with Flask‑SQLAlchemy
- **Migrations**: Alembic via Flask‑Migrate
- **Auth**: Flask‑Login (session auth) + Flask‑JWT‑Extended (token/JWT for APIs)
- **Templating**: Jinja2 (server‑rendered HTML)
- **Background/Tasks**: Synchronous request/response; no task queue by default
- **HTTP Server**: Gunicorn in production
- **Database**:
  - Local/dev: SQLite (`instance/erp_system.db`)
  - Cloud: PostgreSQL (Cloud SQL) via `DATABASE_URL`
- **Containerization**: Docker (slim image), non‑root user, `ENTRYPOINT` script, health endpoint
- **CI/CD + Deployment**:
  - Google Cloud Build → Cloud Run (container image), `cloudbuild.yaml`
  - Alternative k8s manifest (`k8s-deployment.yaml`)
  - `Procfile` for platforms supporting Procfile semantics
- **Reporting/PDFs**: WeasyPrint, xhtml2pdf, ReportLab, pdfkit; digital signatures with pyHanko
- **Data/Excel**: pandas, openpyxl, XlsxWriter, xlrd
- **Localization/RTL PDF**: arabic‑reshaper, python‑bidi

### High‑Level Architecture
- **Application factory**: `app.create_app(config_name)` constructs the Flask app, loads config, wires extensions, registers blueprints, filters, and error handlers.
- **Blueprint‑driven modular monolith**: Each business domain is a Flask blueprint under `modules/*` for isolation and clarity.
- **Database access**: SQLAlchemy models grouped per domain; migrations kept in `migrations/`.
- **Presentation**: Server‑side rendered Jinja2 templates with custom filters (e.g., `nl2br`, `timeago`).
- **APIs**: JWT‑secured endpoints for POS API (`modules/pos/api.py`), plus standard Flask routes.
- **Observability**: `/health` HTTP probe; production logging to stderr.

### Project Structure (selected)
- `app.py`: App factory, blueprint registration, filters, error handlers, dashboard, events/activities routes, `/health`.
- `wsgi.py`: Exposes `application = create_app('production')` for Gunicorn.
- `extensions.py`: Initializes `db`, `migrate`, `jwt`, `login_manager`.
- `config.py`: Environment‑specific config (Development/Testing/Production), database URI selection, upload dirs.
- `modules/*`: Domain modules (auth, inventory, pos, sales, employees, admin, reporting, etc.).
- `migrations/`: Alembic migration scripts.
- `Dockerfile`, `cloudbuild.yaml`, `k8s-deployment.yaml`, `Procfile`: Deployment artifacts.

### Modules and Responsibilities
- `modules/auth`: User models, forms, routes; `load_user` integration; role checks.
- `modules/inventory`: Product catalog, stock moves, warehouse/shop manager flows; multiple blueprints (`inventory_manager_bp`, `shop_manager_bp`, `warehouse_bp`, `scrap_bp`).
- `modules/pos`: POS orders/returns, web UI and `pos_api` for integrations; role‑based access.
- `modules/sales`: Sales dashboards and routes.
- `modules/employees`: Employees, attendance, locations, clock‑in/out; templates for HR flows.
- `modules/reports` and `modules/warehouse_reports`: Reporting routes; PDF/Excel generation via installed libs.
- `modules/admin` and `modules/manager`: Admin utilities and managerial views.
- `modules/notifications`, `modules/help`, `modules/tour`, `modules/settings`: Auxiliary UX features.
- `modules/core`: Shared models such as `Activity` and `Event` used for audit/event views.

### Configuration and Environments
- Config is chosen by `FLASK_CONFIG` (`development`, `testing`, `production`).
- Secrets: `SECRET_KEY`, `JWT_SECRET_KEY` come from environment in production.
- Database selection:
  - Dev/Testing default to SQLite; `instance/` is volume‑mounted in Docker for persistence.
  - Production: `DATABASE_URL` expected (e.g., Cloud SQL Postgres). Fallbacks to file‑based SQLite if not provided.
- Mail config placeholders included for future use (TLS, username/password via env).

### Authentication and Authorization
- **Session auth**: Flask‑Login manages user sessions for server‑rendered routes.
- **JWT auth**: Flask‑JWT‑Extended issues JWTs for API routes (e.g., POS endpoints).
- **Role‑based guards**: Decorators like `sales_worker_forbidden` gate sensitive routes; home route redirects by role (`Sales Worker`, `Shop Manager`, `Inventory Manager`, `Admin`).

### Data Layer and Migrations
- SQLAlchemy models per module. Alembic tracks schema via `Flask-Migrate`.
- Operational scripts in repo (e.g., `init_db.py`, `create_*`, `fix_*`) support data correction and bootstrap workflows.
- Dev bootstrap path: `flask db upgrade` followed by domain initializers (see `Procfile` and scripts).

### Rendering and UX
- Jinja2 templates under `templates/` and module subtrees.
- Global context injectors: `now`, `quote`, user notifications.
- Custom filters: `nl2br`, `timeago` for human‑readable timestamps.
- Minimal front‑end JS; primarily SSR for reliability in constrained environments.

### Reporting, PDFs, and Documents
- Multiple PDF pipelines:
  - **WeasyPrint** for CSS‑aware PDFs.
  - **xhtml2pdf/ReportLab** for templated PDFs where CSS fidelity is less critical.
  - **pdfkit/wkhtmltopdf** available where headless WebKit rendering is needed.
- **Digital signatures**: `pyHanko` and `pyhanko-certvalidator` for signing/validating PDFs.
- **Barcode/QR**: `qrcode`, `pypng` for printable artifacts.
- **Excel/CSV**: `pandas`, `openpyxl`, `XlsxWriter`, `xlrd` for import/export.
- **RTL/International**: `arabic-reshaper`, `python-bidi`, `lxml`, `cssselect2` for multilingual document rendering.

### Deployment and Operations
- **Container**: Python 3.9‑slim base; compilers/dev libs installed only as needed; non‑root `appuser`.
- **Entrypoint**: `docker-entrypoint.sh`; `gunicorn` runs `wsgi:application` on port 8080.
- **Health checks**: `/health` returns JSON with current timestamp; used by Cloud Run/K8s probes.
- **Cloud Build → Cloud Run**: `cloudbuild.yaml` builds, pushes, and deploys image, sets env vars, and attaches Cloud SQL instance.
- **Kubernetes**: Example `Deployment` and `Service` manifest with liveness/readiness probes and secret‑backed `SECRET_KEY`.
- **Procfile**: Example bootstrap (`flask db upgrade && python init_db.py && gunicorn ...`).

### Observability and Reliability
- Logging: Production config adds stream handler to stderr.
- Probes: Liveness/Readiness via `/health`.
- Defensive coding: try/except with DB rollbacks around dashboard and reporting queries to avoid request crashes.

### Security Considerations
- Secrets via environment in production; avoid hardcoded keys outside dev.
- Role checks at route level for sensitive dashboards.
- JWT access tokens with 1‑hour expiry (`JWT_ACCESS_TOKEN_EXPIRES`).
- File uploads constrained by `UPLOAD_FOLDER` and `MAX_CONTENT_LENGTH` (16MB).

### Performance and Scalability Notes
- Stateless containers allow horizontal scaling (Cloud Run concurrency; K8s replicas).
- Database connection managed by SQLAlchemy pool; for Cloud SQL, ensure proper pool sizing (configurable via env).
- Heavy reports can be offloaded to separate worker/service if needed (future work).
- Caching layer (Redis) not currently integrated; candidates include caching read‑mostly queries and template fragments.

### Testing Strategy (current and proposed)
- Current: Ad‑hoc scripts and manual verification; `TestingConfig` uses a separate SQLite DB.
- Proposed:
  - Pytest with Flask app factory fixtures (per‑test transactions or ephemeral DB).
  - FactoryBoy/Seed scripts for domain entities.
  - API tests for `pos_api` with JWT flows.
  - Snapshot tests for HTML templates of critical pages.

### Local Development
1. Create and activate a virtualenv for Python 3.9.
2. `pip install -r requirements.txt`
3. Set environment: `set FLASK_CONFIG=development` (Windows PowerShell) or `export FLASK_CONFIG=development`.
4. Initialize DB: `flask db upgrade` (and run bootstrap scripts as needed, e.g., `python init_db.py`).
5. Run locally: `python app.py` (dev) or `gunicorn wsgi:application -b 0.0.0.0:8080` (prod‑like).

### Notable Design Choices and Trade‑offs
- **Modular monolith with Flask blueprints**: Keeps deployment simple while preserving domain boundaries. Trade‑off: single process/memory space.
- **Server‑side rendering**: Reliability and speed for internal tools without SPA complexity. Trade‑off: fewer rich client interactions.
- **SQLite for dev, Postgres for prod**: Minimal friction locally; ensures robust prod semantics. Trade‑off: some edge‑case differences between engines.
- **Multiple PDF engines**: Flexibility to match use‑case requirements. Trade‑off: larger dependency surface and container size.
- **Cloud Run first**: Simple autoscaling without cluster ops burden. K8s manifest provided for portability.

### Future Improvements
- Add Redis‑backed caching and server‑side session store.
- Introduce task queue (RQ/Celery) for heavy reporting and async jobs.
- Centralize role/permission management and policy tests.
- Structured logging + request IDs; basic metrics (Prometheus or Cloud Monitoring dashboards).
- Hardened CI (lint/test), SAST, container scanning; typed code with mypy.

### Key Files (quick reference)
- `app.py`, `wsgi.py`, `extensions.py`, `config.py`
- `modules/*` (blueprints, models, routes)
- `migrations/`
- `Dockerfile`, `cloudbuild.yaml`, `k8s-deployment.yaml`, `Procfile`


