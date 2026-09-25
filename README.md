# kaix (MarsAIX)

MarsAIX is a Frappe-based industrial AI platform providing feasibility analysis, market
trend insights, vendor/incentive/employment search, and analytics for industrial business
scale planning. This repo (`kaix`) contains the backend Frappe app and its accompanying
React frontend.

## Project Structure

```
kaix/
├── Ai_module/              # AI-driven query classification, feasibility, extraction logic
├── Analytics_module/       # Analytics for approvals, incentives, employment, vendor search
├── Management_Class/       # Orchestration layer wiring AI + Analytics + Redis together
├── Mapping_module/         # Distance / location mapping utilities
├── Market_Trends/          # Market trend scraping, caching, and DB updates
├── Validations/            # Input validation logic per query type
├── Log_management/         # Logging utilities and log storage
├── marsaix/doctype/        # Frappe DocTypes (ai_log, sessions, feasibility reports, etc.)
├── vectors/                # Vector store data (Chroma) — not meant to be version controlled
├── tests/                  # Unit and integration tests
└── www/                    # Frontend entry template served by Frappe

frontend/
├── src/
│   ├── components/         # React UI components (chat, results, maps, forms, etc.)
│   ├── Redux/Store/        # Redux slices and store config
│   └── assets/             # Images, fonts, icons
└── vite.config.js
```

## Requirements

- A working [Frappe/Bench](https://frappeframework.com/) environment
- Node.js (for the frontend build)
- Python 3.10+
- Redis (used by `Management_Class/Redis_management`)
- MariaDB (Frappe's default database)

## Setup

```bash
# From your frappe-bench directory
bench get-app kaix https://github.com/Octo-Advisory/kaix.git
bench --site <your-site> install-app kaix
```

### Frontend

```bash
cd apps/kaix/frontend
npm install
npm run build
```

The build output is served by Frappe via `kaix/public/frontend`.

## Environment / Configuration

This app expects certain runtime configuration (API keys, DB paths, etc.) via Frappe's
site config or environment variables — see `Management_Class/helpers/config.py` for what's
read at runtime. **No secrets, keys, or credentials should be committed to this repo.**

## Development Notes

- Vector data (`kaix/vectors/`) is generated at runtime and should stay out of version
  control — see `.gitignore`.
- Log files (`*.txt`, `*.log`) under various modules are runtime artifacts, not source.

## License

See `LICENSE`.
