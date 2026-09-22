# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`kaix` is a Frappe v15 app (Python ≥3.10) that powers **Mars 2.0 / MarsAIX** — an AI-driven industrial-setup advisor (land, vendors, workforce, incentives, approvals). It is *not* purely a "frontend" despite the name: the Python side under `kaix/` runs all AI/analytics/validation logic; the React SPA under `frontend/` is its UI.

The app is expected to live at `~/frappe-bench/apps/kaix/`. Several modules build absolute paths via `os.path.expanduser("~") + "/frappe-bench/apps/kaix/..."`, so do not move/symlink the tree.

## Commands

All commands assume you are already inside an active `frappe-bench` checkout.

### Frontend SPA (React + Vite, in `frontend/`)
- `cd frontend && yarn install` — install (root-level `npm install` runs this via `postinstall`)
- `yarn dev` — Vite dev server on `:8080`, proxies `/(app|api|assets|files|private)` to the local Frappe webserver (port read from `sites/common_site_config.json`)
- `yarn build` — builds with `--base=/assets/kaix/frontend/`, outputs to `kaix/public/frontend/`, then copies `index.html` to `kaix/www/frontend.html` (the SPA mount point Frappe serves)
- `yarn lint` — ESLint
- No test runner is configured. Root `package.json`'s `test` script is a stub.

### Backend / Frappe
Run from the bench root (`~/frappe-bench`):
- `bench --site <site> install-app kaix` — first install onto a site
- `bench --site <site> migrate` — apply DocType / patches changes
- `bench start` — runs web + workers + redis
- `bench --site <site> console` — Python REPL with `frappe` bootstrapped, useful for testing whitelisted methods
- Logs: `bench --site <site> show-log` (Frappe), plus app-specific output described below

There is no Python test suite wired up in `hooks.py` (`before_tests` is commented out).

## Architecture — the big picture

### SPA ↔ Frappe wiring
- SPA is served at `/frontend/...` paths. `hooks.py` declares `website_route_rules = [{'from_route': '/frontend/<path:app_path>', 'to_route': 'frontend'}]`, which routes everything under `/frontend/*` to `www/frontend.html` (the Vite-built `index.html`).
- The SPA is mounted with `<BrowserRouter basename="/frontend">` (`frontend/src/App.jsx`). Use that prefix when reasoning about route URLs.
- Auth is handled via `frappe-react-sdk` (`useFrappeAuth`); state via Redux Toolkit + `redux-persist` (`frontend/src/Redux/Store/store.js`, slices in `Featuresilces/`).
- Realtime: `socket.io-client`. Backend publishes events via `frappe.publish_realtime` — e.g., `feasibility_update` (Feasibility Report `on_update`, see `Management_Class/helpers/utility.py:send_realtime_update`) and `Property_Seg_Status_Update`.

### Python module layout (only `Frontend` and `marsaix` are registered in `modules.txt`)
- `Ai_module/` — LLM-driven query handling. The orchestrator is `Ai_module/Query_Classification_And_Analysis.py` (instantiates the shared `ChatGroq` LLMs and `RESPONDER_LLM`). Each query *type* has its own subpackage with an `Extraction_for_*.py` entrypoint:
  - `build_from_scratch` → `entry_build_from_scratch`
  - `employement_query` → `call_handle_employment_query`
  - `incentive_query` → `call_incentive_search`
  - `approval_query` → `call_handle_approval_query`
  - `vendor_query` → `call_handle_vendor_query`
  - `feasibility_agentic_workflow/feasibility_agent.py` — `FeasibilityAgent` + `process_agent_result`
  - `Feasibility_Universal_Function/Final_Universal_Function.py` — `ensure_vector_and_update_record` (vector-store side)
  - `responder_consultant.py` — final response polishing layer (`consultant_response_from_langchain` / `_from_strings`)
- `Management_Class/`
  - `Ai_management/AI.py` — top-level façade that imports from all the per-query Extraction modules above and applies `polish_ai_response_if_possible` via the responder consultant
  - `Analytics_management/`, `Redis_management/Redis_chat.py` (chat history + state cache: `save_chat`/`get_chat`/`save_state`/`get_state`)
  - `helpers/utility.py` — grab-bag: `delete_user`, `get_docs_with_children`, `checkApiThreshold` (rate-limits writes to `Api Daily Limit` / `Api Monthly Limit`), `update_llm_token`, `randomSentences` (UI progress strings), `generate_chat_title`, `extract_query_list` / `normalize_queries_with_known_cities` (uses spaCy `en_core_web_sm` GPE NER), `convert_json_to_binary` / `retrieve_and_decompress` (msgpack+gzip+base64 of `tabChat history.result`), `excute_Property_Creation` (subprocess into `~/frappe-bench/AeroShape/FinalCode.py` using `~/property_seg_env/bin/python`, triggered by `trigger_script` via `frappe.enqueue` long queue), `send_realtime_update`, `updateNearestConnectivity` (haversine over Survey No → Railway Station/Substation/Airport/Seaport)
- `Analytics_module/` — analytics counterparts mirroring the same query-type folders
- `Validations/` — per-query validators (`approval_validation.py`, `employeement_validation.py`, `incentive_validation.py`, `vendors_validation.py`, `Validation_for_build_Industry_from_strach.py`, `validate.py`)
- `Mapping_module/` — `distance.py`, `merge.py`
- `Market_Trends/` — market-trend ingestion + DB updates (uses `maria_db.py`, `prompts.py`, `search_cache.json`)
- `marsaix/doctype/` — DocType definitions. The unified log container is **Mars Log** with child tables **Ai Log / Analytics Log / Mapping Log / Validation Log**. Other notable DocTypes: Feasibility Report / Feasibility Json / Feasibility Test, Chat history / Linked Chats / Session / Session State / Progress, Mars Config (LLM token counters + API thresholds), Mars Configurations, UI Configuration(s), Api Daily/Monthly Limit, Aix Diagnostics Hub.
- `vectors/` — persisted vector stores. Note both `Feasibility Report/` (with space) and `Feasibility_Report/` (with underscore) coexist; the underscore variant is the active one written by `ensure_vector_and_update_record`. Don't "clean up" the duplicate without checking call sites.

### Logging — `Log_management/`
- Single entry point: `kaix.Log_management.createlog.log(chatId, level, key, value, file_name, module)` where `module ∈ {ai, analytics, mapping, validation}`.
- Behavior is gated by `Log_management/mars.ini` `[Settings]`:
  - `doc_log = yes` → writes a child row into the matching Mars Log child table (auto-creates the parent Mars Log keyed by `chat_id`)
  - `file_log = yes` → appends one JSON line per call to `/mnt/d/mars_logs/<module>.txt` (hardcoded WSL path — the in-tree `Log_management/<module>.txt` files are leftovers, not the live target)
- `update_config(doc_log, file_log)` rewrites `mars.ini`; `Management_Class/helpers/config.py:update_config(doc)` also writes `[Key].groq_key`.

### Configuration & secrets
- All API keys, base URLs, and the LLM `groq_key` are read from `Log_management/mars.ini` at module import time (e.g., `Query_Classification_And_Analysis.py`, `helpers/utility.py`, `AI.py`). Changing keys requires either editing `mars.ini` directly or going through the `update_config` whitelisted methods — a process restart picks up new values.
- `mars.ini` is currently checked in with live keys (Groq, OpenAI, SerpAPI, multiple Frappe API keys). Treat it as sensitive when sharing diffs.
- Three Frappe API key/secret blocks exist: default app keys, the location-aware logic keys (`portal.marsaix.com`), and per-environment URLs (`mars_live_url`, `local_mars_url`, `ritu_local_base_url`). Pick the right pair for the call site.

### LLMs
Defined once in `Ai_module/Query_Classification_And_Analysis.py`, imported by the rest:
- `llm_70b_vers` (deterministic), `llm_70b_vers_creative` (T=0.7), `llm_8b_inst`, `llm_gpt_oss_120b`, `llm_maverik` — all `ChatGroq`
- `RESPONDER_LLM` — currently `openai/gpt-oss-120b` via Groq, used by `responder_consultant`
- spaCy `en_core_web_sm` is required at import time in `helpers/utility.py` — install with `python -m spacy download en_core_web_sm` if missing.

### Frappe hooks worth knowing
`hooks.py`:
- `doc_events`: `Feasibility Report.on_update → send_realtime_update`
- `website_route_rules`: SPA mount at `/frontend/<path>`
- No `scheduler_events`, `before_tests`, `auth_hooks`, etc. (all commented out)

## Conventions / gotchas

- Whitelisted methods are spread across many files; many use `allow_guest=True`. When adding a new endpoint, prefer placing it next to the relevant module (e.g., a new vendor-search endpoint goes under `Ai_module/vendor_query/` or `Management_Class/helpers/`) and follow the existing `@frappe.whitelist(allow_guest=True)` pattern only if anonymous access is genuinely required.
- Long-running work goes through `frappe.enqueue(... queue='long' ...)` (see `trigger_script`). Don't run heavy AI/subprocess calls inline in a request handler.
- LLM token usage is tracked per-model in the **Mars Config** DocType via `update_llm_token(result, llm=...)` — call this after every `chain.invoke(...)` that returns `usage_metadata`.
- API-rate-limited integrations should go through `checkApiThreshold(apiName)` which reads/updates **Mars Config / Api Daily Limit / Api Monthly Limit**.
- Frontend build's base path is hard-coded to `/assets/kaix/frontend/`. If you change it, update both `frontend/package.json`'s `build` script and any absolute asset references.
- `frontend/src/Redux/Store/Featuresilces/` is misspelled (should be "FeatureSlices") but is referenced by that exact name everywhere — don't rename without sweeping all imports.
