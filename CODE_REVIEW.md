# Code Review: `frontend_app` (Mars 2.0 / MarsAIX)

| | |
|---|---|
| **Repository** | `frappe-bench/apps/frontend_app` |
| **Branch reviewed** | `krunal` (HEAD `e097067`) |
| **Review date** | 2026-04-28 |
| **Scope** | Backend Python (`frontend_app/`) + React SPA (`frontend/`) |
| **Reviewer role** | Senior Engineering Reviewer (read-only audit) |
| **Out of scope** | Underlying Frappe/ERPNext core; vendored `node_modules`; AeroShape script (`~/frappe-bench/AeroShape/FinalCode.py`) referenced as an external dependency |

---

## 1. Executive summary

The application is a Frappe v15 app that pairs an industrial-advisory LLM backend with a React 18 SPA. The product surface is rich — query classification, vector-RAG feasibility studies, geospatial property scoring, market-trends ingestion, real-time progress reporting — and most features clearly work in production. The architecture, however, has accumulated significant technical and **security debt** that should be addressed before further feature work or any external exposure.

The five issues with the highest blast radius are:

1. **Live API secrets are committed to the repo** (`Log_management/mars.ini`) alongside SSH private keys. Rotation alone is not sufficient — git history must also be scrubbed.
2. **An unauthenticated user can delete any account.** `delete_user` is exposed as `allow_guest=True` and uses `ignore_permissions=True`. This is one of 25 guest endpoints, several of which are similarly inappropriate.
3. **SQL injection is reachable** through multiple f-string-formatted `frappe.db.sql` calls in the analytics, market-trends, and build-from-scratch modules.
4. **Frappe API key/secret pairs are baked into the JS bundle** and shipped to every browser, granting client-side identity.
5. **The SPA's `PrivateRoute` does not work.** It is defined but never used, and references an unimported `<Outlet />`. Most "internal" routes are reachable without authentication.

Beyond these P0 items, the codebase has structural problems that compound future risk: four Python files exceed 1,000 lines (one is nearly 5,000), expensive work runs at module-import time on every Frappe worker boot, mid-handler `frappe.db.commit()` calls fragment transactions, bare `except:` swallows failures and reports success, and the React SPA contains five JSX files over 1,400 lines with leaking event listeners.

The code is broadly readable, the per-query module split (`approval_query`, `vendor_query`, `incentive_query`, `employement_query`, `build_from_scratch`) gives natural seams for refactor, and the prompt engineering in `responder_consultant.py` is high-quality. The path to a healthier codebase is clear; this document specifies it.

A prioritized roadmap is given in [Section 7](#7-remediation-roadmap).

---

## 2. Severity rubric

Each finding carries a severity tag. Definitions:

| Severity | Meaning | Response time |
|---|---|---|
| **P0 / Critical** | Exploitable security flaw, data-loss path, or actively-shipping defect with no workaround. | Patch within 1–7 days. Hold feature work if necessary. |
| **P1 / High** | Reliability, correctness, or hardening problem with realistic exploitation/failure scenario. | Patch within current sprint. |
| **P2 / Medium** | Maintainability, performance, or architectural debt that compounds over time. | Schedule into next 1–2 sprints. |
| **P3 / Low** | Polish, minor consistency, or style. | Backlog or fix in passing. |

Categories used in tags: **SEC** (security), **CORR** (correctness), **REL** (reliability/operations), **PERF** (performance), **ARCH** (architecture), **MAINT** (maintainability), **A11Y** (accessibility), **FRAPPE** (Frappe-specific idiom).

---

## 3. Codebase metrics

| Metric | Value |
|---|---|
| Backend Python source | ~37,600 LOC (excluding `__pycache__`) |
| Frontend JS/JSX source | ~27,200 LOC (excluding `node_modules`) |
| Largest Python file | `Ai_module/Query_Classification_And_Analysis.py` — 4,865 LOC |
| Largest JSX file | `components/ResultScreens/Test/NewIndustryScreen.jsx` — 2,050 LOC |
| `@frappe.whitelist` endpoints | 58 |
| `allow_guest=True` endpoints | 25 |
| Files using raw `frappe.db.sql` | 21 |
| DocTypes defined | 22 (all controllers are 9-line stubs) |
| Persisted patches in `patches.txt` | 0 |
| Test files outside Frappe stubs | 0 |

A full inventory of guest endpoints, raw-SQL files, and module-level side effects is given in [Appendices A, B, and C](#appendix-a-guest-endpoints-to-audit).

---

## 4. P0 findings — Critical

### P0-1 — Live secrets committed to source control
**Tags:** SEC · CRIT
**Locations:**
- `frontend_app/Log_management/mars.ini`
- `frappe-bench/apps/frontend_app/KEY`, `KEY.pub`, `id_rsa`, `id_rsa.pub`, `key`, `key.pub`, `ssh_key`, `ssh_key.pub`

**Evidence.** `mars.ini` ships with active credentials for Groq (`groq_key`), OpenAI (`openai_api_key`), SerpAPI (`serpapi_api_key`), and three independent Frappe API key/secret pairs (`frappe_doctype_api_key`, `frappe_api_key`, `location_aware_frappe_api_key`). The repository root additionally contains four pairs of SSH private/public keys.

**Impact.** Any developer (or anyone with read access to the repo, CI artifacts, or a clone) holds full credentials for paid third-party AI services and the production Frappe site. Rotation alone is insufficient: anyone who has ever cloned the repo can walk git history (`git log --all --diff-filter=A -- frontend_app/Log_management/mars.ini`) and recover every superseded value.

**Remediation.**
1. Rotate every key today: regenerate Groq, OpenAI, SerpAPI keys; revoke and reissue all three Frappe API key/secret pairs; rotate every SSH key (and audit `~/.ssh/authorized_keys` on hosts that trusted them).
2. Move all secrets to `frappe.conf` / `site_config.json` / OS environment variables. Read them via `frappe.conf.get("groq_key")` rather than `configparser`.
3. Add `mars.ini`, `KEY*`, `id_rsa*`, `key*`, `ssh_key*` to `.gitignore`.
4. Scrub git history with `git filter-repo --invert-paths --path frontend_app/Log_management/mars.ini --path KEY --path id_rsa --path key --path ssh_key` (and the public counterparts), then force-push and re-clone on every developer machine.
5. Adopt `gitleaks` or `trufflehog` as a pre-commit hook + CI gate so this cannot recur.

---

### P0-2 — Guest endpoint deletes arbitrary users
**Tags:** SEC · CRIT
**Location:** `Management_Class/helpers/utility.py:38-44`

```python
@frappe.whitelist(allow_guest=True)
def delete_user(user_id):
    try:
        frappe.delete_doc('User', user_id, ignore_permissions=True)
        return {'status': 'success', 'message': 'User deleted'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
```

**Impact.** An unauthenticated HTTP request can delete any account, including `Administrator`. Combined with P0-1, this is a complete site compromise.

**Remediation.**
- Remove `allow_guest=True`.
- Drop `ignore_permissions=True` and let Frappe's permission system gate it.
- Restrict to a System Manager role check at the top of the function: `frappe.only_for("System Manager")`.
- Add an audit log entry on every successful deletion.

---

### P0-3 — SQL injection in raw `frappe.db.sql` calls
**Tags:** SEC · CRIT
**Locations (non-exhaustive):**
- `Market_Trends/getting_market_trends.py:176-190` — interpolates `sub_sector`, `segment`, `city`, `state`, `main_industry` via f-string.
- `Analytics_module/incentive_query/incentive_search_query.py:24-27, 43-46, 63-66, 145-208` — six+ f-string conditions including `given_industry_by_user`, `given_sub_sector_by_user`, `given_area_by_user`.
- `Analytics_module/approval_query/approval_search_query.py:28`
- `Analytics_module/vendor_search/vendor_search_query.py`
- `Analytics_module/emplyement_query/employment_search_algorith.py`
- `Ai_module/build_from_scratch/Extraction_for_Building_from_Scratch.py:3688, 3777, 3816, 3851` (the same file uses parameterized form correctly at `:4006` — the team knows the right pattern; these are oversights).

**Evidence sample.**
```python
# Anti-pattern (vulnerable):
query = f"SELECT ... WHERE segment='{segment}' AND sub_sector='{sub_sector}'"
frappe.db.sql(query)

# Correct form, used elsewhere in the same codebase:
frappe.db.sql("SELECT ... WHERE segment=%s AND sub_sector=%s", (segment, sub_sector))
```

**Impact.** All listed sites accept user input through whitelisted endpoints. An attacker can read or modify arbitrary tables, including `tabUser`.

**Remediation.**
1. Convert every f-string-formatted SQL to parameterized form (`%s` + tuple) or to `frappe.qb` / `frappe.db.get_list` / `frappe.db.get_value`.
2. Add a CI lint rule that fails on `frappe.db.sql\(\s*f["']` (regex). Example with `ruff`/`grep -rn`:
   ```bash
   ! grep -rn --include='*.py' 'frappe\.db\.sql(\s*f["'\'']'  frontend_app/
   ```
3. Audit the 21 files listed in [Appendix B](#appendix-b-files-using-raw-frappe-db-sql) systematically.

---

### P0-4 — Frappe API tokens hardcoded into client bundle
**Tags:** SEC · CRIT
**Locations:**
- `frontend/src/components/MapComponent/service/apiservice.js:4` — `d3de1e0e4e25846:5045c3c55690e0b`
- `frontend/src/components/ResultScreens/Industryresult.jsx:28` — `d3de1e0e4e25846:a17a89fc01bd744` in an `Authorization: token …` header
- `frontend/src/components/Signup/Signup.jsx:172` (commented) — historical residual token

**Impact.** Anyone who opens DevTools or downloads the bundle can replay any API call as the holder of these keys. This is qualitatively different from a public Mapbox token: Frappe API keys grant write access to DocTypes.

**Remediation.**
1. Rotate the affected Frappe API key/secret pairs.
2. Standardize on the pattern already used in `MapComponent.jsx:101` — fetch tokens at runtime via `useFrappeGetDoc("Mars Configurations", "admin_token")`. Even better, move sensitive calls behind a server-side whitelisted endpoint that uses the *server's* credentials.
3. Add a `gitleaks` rule for the `[a-z0-9]{15}:[a-z0-9]{15}` Frappe-token shape, applied to both `frontend/` and the Python tree.

---

### P0-5 — `PrivateRoute` is a no-op and would crash if used
**Tags:** SEC · CORR · CRIT
**Location:** `frontend/src/App.jsx:25-29, 44-69`

**Evidence.**
```jsx
const PrivateRoute = () => {
  const { currentUser, isValidating } = useFrappeAuth();
  if (isValidating) return <div>Loading...</div>;
  return currentUser ? <Outlet /> : <Navigate to="/login" replace />;
};
```
- `Outlet` is **never imported** from `react-router-dom`.
- The route table never wraps any `<Route>` in `<PrivateRoute>`.

**Impact.** Routes such as `/progress`, `/solution`, `/map`, `/property`, `/details`, `/temp` are reachable without authentication — anyone who knows the URL can navigate. If someone enables `PrivateRoute` without noticing the missing import, the SPA throws on first protected render.

**Remediation.**
```jsx
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";

// Then in the route table:
<Route element={<PrivateRoute />}>
  <Route path="/progress/:sessionId?" element={<ProgressScreen />} />
  <Route path="/property/:id" element={<Property />} />
  {/* …other internal routes… */}
</Route>
```
Add an integration test that hits each protected route with no session and asserts a redirect to `/login`.

---

## 5. P1 findings — High

### P1-1 — Race condition in `checkApiThreshold`
**Tags:** CORR · REL · FRAPPE
**Location:** `Management_Class/helpers/utility.py:77-166`

The function reads `Api Daily Limit.count`, compares to `dailyMaxLimit`, then increments. There is no row-level lock between read and write. Two concurrent requests can both pass the cap check and both increment, exceeding the limit. Also, manual `frappe.db.commit()` is called multiple times mid-function (`:110, 132, 145, 165`) so partial counter writes survive a later failure.

**Remediation.** Replace the read–check–write with one atomic UPDATE that returns affected-row count, e.g.:

```python
rows = frappe.db.sql("""
    UPDATE `tabApi Daily Limit`
    SET count = count + 1, modified = NOW()
    WHERE name = %s AND count < %s
""", (limit_doc_name, daily_max_limit))

if not frappe.db.sql_last_row_count():
    return False  # cap exceeded
```

Hold a single commit at the end; do not commit mid-function.

---

### P1-2 — Mid-handler `frappe.db.commit()` proliferation
**Tags:** REL · FRAPPE
**Locations:**
- `Log_management/createlog.py:41, 58`
- `Management_Class/helpers/utility.py:110, 132, 145, 165, 179, 737, 826`
- `Mapping_module/distance.py:151`
- `Mapping_module/merge.py:216, 232, 244` — `:244` is **inside a delete loop**, so an exception mid-loop leaves a half-deleted set
- `Market_Trends/getting_market_trends.py:95`

**Impact.** Frappe commits the transaction automatically on a successful request. Manual commits split a single user request into multiple independent transactions. If a later step fails, the application is left in an inconsistent intermediate state (orphan log rows, partial counters, half-merged property records).

**Remediation.** Remove all manual commits unless there is a documented reason (e.g. before a long blocking external call where you need durability). Where a comment is justified, write one explaining the *why*.

---

### P1-3 — Bare `except:` swallowing failures and reporting success
**Tags:** CORR · REL
**Locations:**
- `Final_Universal_Function.py:203, 396, 425, 652` — bare `except:` returning `True`.
- `Analytics_module/incentive_query/incentive_search_query.py:19-20`
- `Analytics_module/approval_query/approval_search_query.py:30`
- `Analytics_module/vendor_search/vendor_search_query.py:21`
- `Ai_module/vendor_query/Extraction_for_vendor_search.py:31`
- `Ai_module/build_from_scratch/Extraction_for_Building_from_Scratch.py:444`
- `Management_Class/Ai_management/AI.py:95-96` — `polish_ai_response_if_possible` swallows everything and returns the unpolished response with no signal that polishing failed.

**Impact.** Silent failure modes are the hardest class of bug to diagnose. Bare `except:` also masks `KeyboardInterrupt` and `SystemExit`, making bench restarts and Ctrl-C unreliable.

**Remediation.**
- Catch only specific exception types you can handle.
- Always `frappe.log_error(traceback.format_exc(), title="…")` on the catch.
- Return a uniform error envelope, never a fake-success.
- Add a project-wide lint rule (`ruff` rule `E722`) banning bare except.

---

### P1-4 — Module-import-time side effects
**Tags:** REL · PERF · ARCH
**Locations:**
- `Ai_module/Query_Classification_And_Analysis.py:24-37, 53` — instantiates 7 `ChatGroq` clients + `RESPONDER_LLM` at import time, plus reads `mars.ini`.
- `Ai_module/Query_Classification_And_Analysis.py:104` — `spacy.load("en_core_web_lg")` (~600 MB).
- `Analytics_module/incentive_query/incentive_search_query.py:6` — second `spacy.load("en_core_web_lg")`.
- `Management_Class/helpers/utility.py:30-32, 35-36, 560` — reads `mars.ini`, instantiates two `ChatGroq` clients, loads `en_core_web_sm`.

**Impact.**
- Cold imports take seconds; every gunicorn worker pays that cost on boot, every `bench restart` lengthens.
- Two distinct copies of `en_core_web_lg` reside in memory per process.
- If `mars.ini` is missing or unreadable, *every* import in the application fails. There is no graceful degradation path.

**Remediation.**
- Lazy-init LLM clients via a cached factory: `@functools.lru_cache; def get_llm(name: str) -> ChatGroq: …`.
- Centralize spaCy in one helper module (`nlp_models.py`) and have callers import the loaded singleton.
- Read configuration through a function (`get_config()`) that raises a controlled error at *call* time, not at import time.

---

### P1-5 — LLM responses parsed via regex + `ast.literal_eval`
**Tags:** CORR · REL
**Locations:**
- `Management_Class/helpers/utility.py:546-554`
- `Ai_module/Query_Classification_And_Analysis.py:1601, 1612, 1622`

**Impact.** `ast.literal_eval` is safer than `eval` but still raises on any non-literal output, and the failure paths return inconsistent shapes (sometimes a list, sometimes a string error message). Downstream callers cannot reliably distinguish "no results" from "parser failed."

**Remediation.**
- Use Groq's structured-output mode (`response_format={"type": "json_object"}`) where supported.
- Validate every parsed payload through a `pydantic` model at the boundary.
- On parse failure, retry once with a corrective prompt that includes the raw output and the validation error; if the retry also fails, return a typed error envelope.

---

### P1-6 — N+1 query patterns
**Tags:** PERF · FRAPPE
**Locations:**
- `Management_Class/helpers/utility.py:62-64` — `get_docs_with_children` loops `frappe.get_doc(doctype, name)` per name. For a page that batches 50 vendors, that is 50 individual round-trips.
- `Management_Class/helpers/utility.py:925-966` — `updateNearestConnectivity` fetches *all* Survey Nos, then for each Survey No fetches *all* rows of 4 doctypes with `fields=['*']`. With 1,000 properties this is ~4,000 full-table reads.
- `Management_Class/helpers/utility.py:924, 926` — `frappe.log_error` used as info logging in the same loop, flooding the Error Log table.

**Remediation.**
- For `get_docs_with_children`: a single `frappe.get_list(doctype, filters=[["name", "in", names]], fields=[…])` followed by one bulk fetch per child table.
- For `updateNearestConnectivity`: load each ancillary doctype once, build a `scipy.spatial.cKDTree` keyed on coordinates, then query per-survey in O(log n). Replace `frappe.log_error` with `frappe.logger().info`.

---

### P1-7 — React effect leaks in map and chat components
**Tags:** CORR · PERF
**Locations:**
- `frontend/src/components/MapComponent/MapComponent.jsx:535-733` — `addEventListener` on dynamically-created marker DOM elements with no `removeEventListener` in cleanup.
- `frontend/src/components/MapComponent/MapComponent.jsx:114-115` — direct `document.querySelector` mutations bypassing React's tree.
- `frontend/src/components/Chatscreen/Chatscreen.jsx:272-287, 953-, 966-992` — async `call.get()` fires `setState` after navigation away (no `AbortController`).
- `frontend/src/components/Chatscreen/Chatscreen.jsx:64-77` — `useEffect` reads `sendMsg, messageToSet, passedIntension, location, navigate` but the deps array contains only `[sendMsg]` (stale closure).

**Impact.** Memory leaks on map remounts; "can't perform a state update on an unmounted component" warnings; subtle navigation bugs because effects observe stale `location`.

**Remediation.**
- Every effect that subscribes must return a cleanup that unsubscribes (`addEventListener`/`removeEventListener`, `map.remove()`, `socket.off()`, `clearInterval`, `controller.abort()`).
- Enable the `react-hooks/exhaustive-deps` ESLint rule (already present in dev deps) and resolve all warnings before merge.

---

### P1-8 — Subprocess invocation with user-influenced arguments
**Tags:** SEC · REL
**Location:** `Management_Class/helpers/utility.py:838-866` (`excute_Property_Creation`), enqueued from `:870` (`trigger_script`).

```python
args = [python_exe, script_path, method_name]
if param is not None: args.append(str(param))
if childBlockId is not None: args.append(str(childBlockId))
result = subprocess.run(args, check=True, capture_output=True, text=True, cwd=file_path)
```

**Impact.** No `shell=True` is used today, so this is not direct command injection. However:
- `method_name` is dispatched inside `FinalCode.py` as a function selector with no documented allowlist. If `FinalCode.py` ever maps it to `os.system`/`shell=True`, the chain becomes RCE.
- Hardcoded `~/property_seg_env/bin/python` and `~/frappe-bench/AeroShape` paths break under containerization or any non-`marsaiae` user.
- No timeout on `subprocess.run`; a hung script blocks the worker.

**Remediation.**
- Validate `method_name` against an explicit allowlist in this function.
- Type-coerce `param` and `childBlockId` (e.g., `int(childBlockId)`).
- Add `timeout=` to `subprocess.run` and handle `TimeoutExpired`.
- Move paths into config.

---

### P1-9 — Realtime delivery condition excludes worker-driven updates
**Tags:** CORR · UX
**Location:** `Management_Class/helpers/utility.py:880-892`

```python
def send_realtime_update(doc, method=None):
    current_user = frappe.session.user
    if current_user == doc.owner:
        frappe.publish_realtime(..., user=current_user)
```

**Impact.** Most updates to `Feasibility Report` happen inside the `frappe.enqueue`-d background job, where `frappe.session.user` is `Administrator`, not the owner. The condition silently fails and the SPA never receives the `feasibility_update` event.

**Remediation.** Drop the equality check and always target the owner:
```python
frappe.publish_realtime(
    event="feasibility_update",
    message={"docname": doc.name, "status": doc.status},
    user=doc.owner,
)
```

---

### P1-10 — Liberal use of `ignore_permissions=True`
**Tags:** SEC
**Locations:**
- `Log_management/createlog.py:56`
- `Management_Class/helpers/progress.py:78, 105, 117`
- `Management_Class/Ai_management/feasibility.py:33, 111, 131`
- `Management_Class/Ai_management/helper_ai_for_agents.py:341`
- `Mapping_module/merge.py:243`
- `Market_Trends/getting_market_trends.py:134`

**Impact.** Each call bypasses Frappe's permission system. Many were added to make `allow_guest=True` endpoints work; once those endpoints are properly authenticated (see [Appendix A](#appendix-a-guest-endpoints-to-audit)), most of these can be removed. Each remaining one should carry a comment explaining *why* the bypass is required.

---

### P1-11 — `frappe.log_error(title, message)` argument order misuse
**Tags:** REL · FRAPPE
**Locations:** `Management_Class/helpers/utility.py:121, 154, 313, 924, 926` and others.

**Evidence.** Calls of the form `frappe.log_error("send email daily limit exceed")` or `frappe.log_error("Total Property to Update", len(surveyNoList))` pass the long descriptive string as the *title* and the value as the *message*. In older Frappe versions the title is truncated to 140 characters; even in v15 the columns are reversed in the Error Log UI. A grep for all `frappe.log_error\(` calls and a quick reorder would correct this.

---

### P1-12 — Wildcard imports break refactoring tools
**Tags:** ARCH · MAINT
**Locations:**
- `Management_Class/Ai_management/AI.py:6` — `from frontend_app.Ai_module.Query_Classification_And_Analysis import *`
- `Ai_module/build_from_scratch/Extraction_for_Building_from_Scratch.py:7, 11`
- `Ai_module/approval_query/Extraction_for_approval_search.py:8`

**Impact.** A wildcard import from a 4,865-line module pulls hundreds of names into the consumer's namespace. Renames in the source module break consumers silently at *runtime*, not at import. IDE go-to-definition and dead-code analysis become unreliable.

**Remediation.** Make every import explicit. The first replacement is mechanical: run the consumer once, log every `dir()` name actually used, and write the explicit imports.

---

### P1-13 — SPA persists large blob slices to localStorage
**Tags:** REL · PERF
**Location:** `frontend/src/Redux/Store/store.js`

`redux-persist` defaults to `localStorage`, capped at ~5 MB per origin. Slices like `chat`, `aiResponse`, `analyticsResult`, and `Feasibility` may carry large response blobs (the backend stores chat history as msgpack+gzip+base64). Once a long chat is reloaded into Redux and persisted, subsequent writes will silently fail or evict, leading to non-reproducible "I lost my chat" reports.

**Remediation.**
- `whitelist` only the slices that genuinely need persistence (UI toggles, theme, last-session-id), not chat content.
- For chat history, store only `sessionId` in Redux; fetch full history on demand.
- Or switch the persistence store to `localforage` (already a dependency) for IndexedDB-backed capacity.

---

## 6. P2 findings — Medium

### P2-1 — Monolithic files
**Tags:** ARCH · MAINT

| File | LOC | Recommended split |
|---|---|---|
| `Ai_module/Query_Classification_And_Analysis.py` | 4,865 | `llm_clients.py`, `prompts/`, `classifier.py`, `query_refinement.py`, `parsers.py`, `intent_detection.py` |
| `Ai_module/Feasibility_Universal_Function/Final_Universal_Function.py` | 1,806 | `vector_store.py`, `encoders.py`, `record_sync.py` |
| `Ai_module/approval_query/Extraction_for_approval_search.py` | 1,518 | `extraction.py`, `prompts.py`, `dataloaders.py` (mirror across the four query types) |
| `Ai_module/feasibility_agentic_workflow/feasibility_agent.py` | 1,002 | `agent.py`, `tools.py`, `prompts.py`, `result_processing.py` |
| `Management_Class/helpers/utility.py` | 978 | `users.py`, `chat_history.py`, `rate_limit.py`, `geo.py`, `subprocess_jobs.py`, `query_hints.py`, `realtime.py` |
| `frontend/src/components/ResultScreens/Test/NewIndustryScreen.jsx` | 2,050 | extract `Sidebar`, `Modal`, `PropertyList`, `FilterBar`; split state into custom hooks |
| `frontend/src/components/ResultScreens/IndustryResultScreen.jsx` | 1,957 | as above |
| `frontend/src/components/MapComponent/MapComponent.jsx` | 1,940 | hook `useMapboxMap`, `useMarkerLayer`, `usePolygonDraw`; render-only top-level |
| `frontend/src/components/MapComponent/SingleMap.jsx` | 1,622 | as above |
| `frontend/src/components/Chatscreen/Chatscreen.jsx` | 1,476 | extract `MessageList`, `Composer`, `HintsRail`, `IntentBanner` |

**Approach.** Do not attempt a single big-bang refactor. For each file: (1) identify section boundaries by reading `outline` of declarations; (2) extract a leaf module; (3) update imports; (4) commit; (5) repeat. Keep public function signatures stable until the split is complete.

---

### P2-2 — Dead and backup code
**Tags:** MAINT

- `frontend/src/components/ResultScreens/Test/backup1.jsx` (1,412 LOC) — unreferenced.
- `frontend/src/components/ResultScreens/temp.jsx`, `frontend/src/components/Home/Temp.jsx` (imported as both `Temp` and `ChatApp` in `App.jsx`), `frontend/src/components/TestComponent/temp.jsx`, `Test.jsx`, `TestComponent.jsx`.
- `Ai_module/Feasibility_Universal_Function/trila.py`, `Log_management/testlog.txt`.
- `Management_Class/helpers/utility.py:629-684` — 55 lines of commented-out duplicate of `convert_json_to_binary` immediately above its live replacement at `:685`.
- Ad-hoc on-disk logs: many handlers append to `testlog.txt` and `log2.txt` in the bench cwd (e.g., `AI.py:136-137, 217, 235, 299, 306, 310-311`). These accumulate forever in production.

**Remediation.** Delete; git history is the backup. Replace ad-hoc file writes with `frappe.logger()` or the existing `Log_management.createlog.log` helper.

---

### P2-3 — Misspellings baked into module paths
**Tags:** MAINT

- `Ai_module/employement_query/Extraction_for_employement_search.py` — "employement" (×2 misspellings of "employment")
- `Analytics_module/emplyement_query/employment_search_algorith.py` — "emplyement" (different misspelling) + "algorith" missing terminal "m"
- `Validations/Validation_for_build_Industry_from_strach.py` — "strach"
- `frontend/src/Redux/Store/Featuresilces/` — should be `FeatureSlices/`

**Impact.** Search across the codebase requires knowing every misspelling. New developers waste time reconciling them.

**Remediation.** One PR with mass rename + import sweep. Do this *before* the next round of feature work — every new file imported from a misspelled folder makes the rename more expensive.

---

### P2-4 — Duplicate vector-store directories
**Tags:** MAINT

`vectors/Feasibility Report/` (with space) and `vectors/Feasibility_Report/` (with underscore) coexist. `ensure_vector_and_update_record` writes to the underscore variant. Either delete the legacy space-named directory after confirming no code reads from it, or move all content under one canonical name.

---

### P2-5 — DocType controllers are empty stubs
**Tags:** FRAPPE · ARCH
**Location:** Every `marsaix/doctype/*/<doctype>.py`.

All controllers are the auto-generated 9-line `class X(Document): pass`. Validation logic instead lives in handlers across `Management_Class/`. This is an opportunity, not just a smell:

- `Mars Config` should validate `daily_min_count <= daily_max_count` and reject negative thresholds.
- `Api Daily Limit` / `Api Monthly Limit` should validate `count >= 0` and have a unique constraint on `(api_id, date)`.
- `Feasibility Report` has business state (`status`) — the `on_update` event would be cleaner as a controller method than a hooked free function.

---

### P2-6 — Duplicate UI primitive libraries
**Tags:** PERF · MAINT
**Location:** `frontend/package.json`

The SPA depends on Tailwind + Material Tailwind + shadcn/ui + Radix + Headless UI + Chart.js + Recharts + Mapbox + Leaflet (+ react-leaflet) + GSAP + Framer Motion + Swiper + Embla. Every redundant library adds first-load JS, parser cost, and cognitive load.

**Suggested rationalization.**
- Maps: drop Leaflet + react-leaflet if all maps render through Mapbox (verify with `grep -rln "react-leaflet" frontend/src`).
- Charts: pick one of Chart.js or Recharts.
- Animation: pick one of GSAP or Framer Motion.
- Carousel: pick one of Swiper or Embla.
- UI primitives: pick one of Material Tailwind, shadcn, Radix, Headless UI as the primary; allow others only as fallbacks for unique components.

Each removal saves real KB on first load and removes a future security-update obligation.

---

### P2-7 — `key={index}` on dynamic lists
**Tags:** CORR (subtle)
**Locations:**
- `IndustryResultScreen.jsx:1376-1378, 1492-1493, 1579-1588, 1706-…`
- `NewIndustryScreen.jsx:1136, 1338, 1379`
- `Vendorresult.jsx:991, 1011`

When the list reorders (filter, sort, paginate) React reuses the wrong component instances, leading to stale internal state in row-level UI. Use a stable id from the data (`solution.name`, `vendor.name`).

---

### P2-8 — Inline functions and missing memoization in giant render trees
**Tags:** PERF
**Locations (illustrative):**
- `IndustryResultScreen.jsx:1378` — `onClick={() => setSelectedProperty(solutions[index])}` recreated each render.
- `MapComponent.jsx` — `draw()` function defined in render scope; if passed to a layer or used in deps array of any effect, every render rebuilds the layer.

**Remediation.** Wrap heavy callbacks in `useCallback` with stable deps; wrap derived data (filtered lists) in `useMemo`. Particularly important when the parent re-renders on every keystroke (Chatscreen, FilterBar).

---

### P2-9 — `redux-persist` and `useToggleState` duplicate persistence paths
**Tags:** ARCH

`useToggleState.js` persists toggle state to `js-cookie` while Redux persists slices to `localStorage`. Two systems means two failure modes and two mental models. Consolidate into Redux (or a single Zustand store, if Redux feels heavyweight for the scope).

---

### P2-10 — `<ErrorBoundary>` imported but commented out
**Tags:** REL
**Locations:** `frontend/src/App.jsx:38`, `frontend/src/main.jsx:28`

A React error in `MapComponent` or `IndustryResultScreen` will currently take down the entire SPA. Re-enable the ErrorBoundary, route it to a friendly fallback, and report the caught error to a logging endpoint.

---

### P2-11 — Hardcoded WSL/user paths
**Tags:** REL · MAINT

Direct dependencies on the host environment:
- `Log_management/createlog.py:71` — `/mnt/d/mars_logs`
- `Management_Class/helpers/utility.py:28-29, 838-844` — `~/property_seg_env`, `~/frappe-bench/AeroShape`
- `Management_Class/helpers/config.py:7`
- `Ai_module/Query_Classification_And_Analysis.py:23-26`

These will break on the first non-WSL deployment, container, or non-`marsaiae` user. Replace with `frappe.get_app_path("frontend_app", …)`, `frappe.utils.get_bench_path()`, and a configurable log root in `site_config.json`.

---

### P2-12 — Empty `patches.txt`
**Tags:** FRAPPE · REL

If any DocType field has been added, renamed, or had its type changed since the first install, fresh-install sites and migrated sites will diverge. Every schema change should have a versioned patch. Even if no past patches were written, future-you needs the discipline.

---

## 7. P3 findings — Low

| # | Tag | Location | Note |
|---|---|---|---|
| P3-1 | A11Y | `IndustryResultScreen.jsx:1295-1322` | `<img>` tags lack `alt` attributes. |
| P3-2 | A11Y | `IndustryResultScreen.jsx:1368-1371, 1378, 1598, 1782-1791` | `<div onClick>` styled as buttons; use `<button type="button">` for keyboard / screen-reader support. |
| P3-3 | MAINT | `frontend_app/__pycache__` is checked into the repo (committed) | Add `__pycache__/` to `.gitignore` and remove from history. |
| P3-4 | FRAPPE | `hooks.py` declares only one `doc_event` (Feasibility Report on_update) | Other DocTypes (`Mars Log`, `Chat history`) have similar lifecycle needs. |
| P3-5 | MAINT | Naming convention drift | `Ai_module`, `Management_Class`, `Mapping_module` mix `PascalCase` and `snake_case` package names. Pick one. |
| P3-6 | MAINT | `kb.py` at `frontend_app/kb.py` | Tiny file — purpose unclear from name; either rename meaningfully or fold into a parent module. |
| P3-7 | REL | LangChain / Groq versions are not pinned in `requirements.txt` | Pin to known-good versions; both libraries have made breaking changes recently. |
| P3-8 | A11Y | `<button>` elements without `type=` default to `type="submit"` inside a form | Audit forms in `Login`, `Signup`, `ForgotPassword`. |
| P3-9 | MAINT | Mixed `console.log`, `print`, `frappe.log_error` for ad-hoc debugging | Standardize on one logger per layer. |
| P3-10 | MAINT | Several whitelisted endpoints have no docstring or type hints | Add minimal docstrings; they become the OpenAPI source of truth if that ever happens. |

---

## 8. Cross-cutting recommendations

### 8.1 CI gates
The codebase is past the size where ad-hoc review can catch regressions. Recommended pipeline additions:

| Gate | Tool | Purpose |
|---|---|---|
| Secret scan | `gitleaks` (or `trufflehog`) | Block keys/SSH material on every push and PR. |
| SQL-injection lint | custom `grep` rule + `bandit` `B608` | Fail on `frappe.db.sql\(\s*f["']`. |
| Python lint | `ruff` with `E722` (bare except), `S` rules (bandit-equivalent) | Catch P1-3, P2-3, P3 items. |
| Type-check | `mypy --strict` on new modules, gradual adoption elsewhere | Prevent shape drift in LLM-parsed payloads. |
| Frontend lint | `eslint --max-warnings=0` with `react-hooks/exhaustive-deps`, `jsx-a11y` | Catch P1-7, P2-7, P3-1, P3-2. |
| Import hygiene | `ruff` `F401`, `F403` | Catch wildcard imports (P1-12) and unused imports. |
| Bundle budget | `vite build` + `rollup-plugin-visualizer` budget check | Prevent bundle regression after dependency rationalization. |

### 8.2 Security baseline
- Make `allow_guest=True` require a code-review label (`requires-security-review`).
- Document an authentication policy: every new endpoint defaults to authenticated; guest is opt-in with a written justification.
- Adopt `frappe.has_permission(doctype, doc=…)` checks at the top of every endpoint that touches DocTypes.
- Add CSP headers via Frappe's `website_context` to mitigate the residual XSS surface from `dangerouslySetInnerHTML`.

### 8.3 Observability
- Standardize on `frappe.logger("frontend_app.<module>")` instead of mixed `print` / `frappe.log_error` / file writes.
- Track LLM call latency, token cost, and parse-failure rate as metrics, not as ad-hoc Mars Config counters.
- Surface the Mars Log child tables in a Frappe report so the team has a self-serve view; right now log inspection requires DocType browsing.

### 8.4 Testing
There are zero non-stub tests today. A pragmatic starting set:
- Unit tests for `responder_consultant.flatten_*`, `remove_last_ai_turn_*` — pure functions, easy wins.
- Unit tests for the LLM-output parsers (after introducing pydantic models).
- Integration test for `ai_module_call` happy path with a stubbed LLM client.
- Cypress / Playwright smoke test for the SPA routes that should require auth (P0-5).

---

## 9. Remediation roadmap

A realistic sequence. Each phase is independently shippable.

### Phase 0 — Stop the bleeding (1–3 days)
1. Rotate every secret in `mars.ini` and every SSH key in the repo root.
2. Move secrets to `frappe.conf` / env vars; delete committed `.ini` and key files.
3. Scrub git history of secret files; force-push; instruct all developers to re-clone.
4. Patch `delete_user`: remove `allow_guest`, drop `ignore_permissions`, gate by role.
5. Patch the SPA hardcoded Frappe tokens: rotate tokens, switch to runtime fetch.
6. Fix the `PrivateRoute` import + wrap protected routes.
7. Add `gitleaks` to CI.

### Phase 1 — Close the security gap (1 sprint)
1. Audit and remediate all 25 `allow_guest=True` endpoints ([Appendix A](#appendix-a-guest-endpoints-to-audit)).
2. Convert every f-string-formatted SQL to parameterized form ([Appendix B](#appendix-b-files-using-raw-frappe-db-sql)).
3. Replace bare `except:` (P1-3); enable `ruff E722`.
4. Add `useEffect` cleanups to `MapComponent` and `Chatscreen` (P1-7).
5. Lazy-init LLM clients and spaCy (P1-4).

### Phase 2 — Reliability (2 sprints)
1. Eliminate mid-handler `frappe.db.commit()` (P1-2).
2. Atomic `checkApiThreshold` (P1-1).
3. Structured-output LLM parsing with pydantic (P1-5).
4. Replace N+1 patterns (P1-6).
5. Switch SPA persistence away from blob slices (P1-13).
6. Fix `send_realtime_update` owner condition (P1-9).

### Phase 3 — Architecture (ongoing)
1. Split the four monoliths along the seams in [P2-1](#p2-1--monolithic-files).
2. Mass rename of misspelled module paths (P2-3).
3. Delete dead/backup files (P2-2).
4. Rationalize duplicate UI libraries (P2-6).
5. Fill in DocType controllers (P2-5).

### Phase 4 — Polish (ongoing)
- All P3 items, accessibility fixes, naming-convention normalization, version pinning.

---

## 10. Tooling / process recommendations

- **Pull-request template** with explicit boxes for: "any new `allow_guest`?", "any new `frappe.db.sql`?", "any new `ignore_permissions`?". Forces conscious decisions.
- **Pre-commit hooks** (`pre-commit` framework): `gitleaks`, `ruff`, `eslint`, formatter.
- **Architecture decision records** in `docs/adr/` for at least the four largest existing modules — a one-page record per module explaining why it exists and what its boundaries are. This makes the next "should this go here?" decision easier.
- **Dependency upgrade cadence** — none of `langchain`, `langchain-groq`, `frappe-react-sdk` are pinned. Adopt Renovate or Dependabot with weekly PRs.

---

## Appendix A — Guest endpoints to audit

The 25 `allow_guest=True` endpoints in the codebase. Each row should be triaged into one of: *keep guest* (with documented reason), *require login*, or *delete*.

| File | Endpoint | First-pass verdict |
|---|---|---|
| `Management_Class/helpers/utility.py:38` | `delete_user` | Remove guest **(P0-2)** |
| `Management_Class/helpers/utility.py:236` | `generate_chat_title` | Require login |
| `Management_Class/helpers/utility.py:325` | `generate_query_hints` | Require login |
| `Management_Class/helpers/utility.py:573` | `normalize_queries_with_known_cities` | Require login |
| `Management_Class/helpers/utility.py:685` | `convert_json_to_binary` | Require login |
| `Management_Class/helpers/utility.py:747` | `retrieve_and_decompress` | Require login |
| `Management_Class/helpers/utility.py:783` | `insert_solution_result` | Require login |
| `Management_Class/helpers/utility.py:837` | `excute_Property_Creation` | Require login |
| `Management_Class/helpers/utility.py:869` | `trigger_script` | Require login |
| `Management_Class/helpers/utility.py:874` | `UpdatePropertySegStatus` | Require login |
| `Management_Class/helpers/utility.py:879` | `send_realtime_update` | Internal — not whitelisted directly |
| `Management_Class/helpers/utility.py:914` | `updateNearestConnectivity` | System Manager only |
| `Management_Class/helpers/utility.py:969` | `findCenterPoint` | Require login |
| `Log_management/createlog.py:13` | `log` | Internal — drop `allow_guest` |
| `Log_management/createlog.py:81` | `update_config` | System Manager only |
| `Management_Class/helpers/config.py:11` | `update_config` | System Manager only |
| `Management_Class/helpers/otp.py:*` | OTP send/verify | Keep guest (login flow) — with rate limit |
| `Management_Class/Ai_management/AI.py:98` | `ai_module_call` | Require login |
| (… plus 7 more across `Ai_module/*` extraction handlers …) | | Require login unless explicit reason |

The exact list should be regenerated with:
```bash
grep -rn --include='*.py' 'allow_guest=True' frontend_app/
```

---

## Appendix B — Files using raw `frappe.db.sql`

All 21 files. Audit each for f-string formatting; convert to parameterized form.

```
Analytics_module/emplyement_query/employment_search_algorith.py
Analytics_module/incentive_query/incentive_search_query.py
Analytics_module/Industry_form_scratch/query_to_build_industry_from_scratch.py
Analytics_module/approval_query/approval_search_query.py
Analytics_module/vendor_search/vendor_search_query.py
Ai_module/approval_query/Extraction_for_approval_search.py
Ai_module/build_from_scratch/Extraction_for_Building_from_Scratch.py
Ai_module/employement_query/Extraction_for_employement_search.py
Ai_module/incentive_query/Extraction_for_incentive_search.py
Ai_module/Query_Classification_And_Analysis.py
Ai_module/vendor_query/Extraction_for_vendor_search.py
Management_Class/Ai_management/AI.py
Management_Class/Ai_management/helper_ai_for_agents.py
Management_Class/helpers/progress.py
Management_Class/helpers/utility.py
Mapping_module/                 (distance.py / merge.py — verify)
Market_Trends/getting_market_trends.py
Validations/approval_validation.py
Validations/employeement_validation.py
Validations/incentive_validation.py
Validations/Validation_for_build_Industry_from_strach.py
Validations/vendors_validation.py
```

---

## Appendix C — Module-level side effects inventory

Functions and classes are fine at module top level. The following are not, and should be deferred to first-call:

| Location | Side effect | Severity |
|---|---|---|
| `Ai_module/Query_Classification_And_Analysis.py:23-37, 53` | reads `mars.ini`; instantiates 7 ChatGroq + 1 RESPONDER_LLM | High |
| `Ai_module/Query_Classification_And_Analysis.py:104` | `spacy.load("en_core_web_lg")` | High |
| `Analytics_module/incentive_query/incentive_search_query.py:6` | second `spacy.load("en_core_web_lg")` | High |
| `Management_Class/helpers/utility.py:28-32` | reads `mars.ini` | Medium |
| `Management_Class/helpers/utility.py:35-36` | instantiates 2 ChatGroq clients | Medium |
| `Management_Class/helpers/utility.py:560` | `spacy.load("en_core_web_sm")` | Medium |
| `Management_Class/helpers/config.py:6-9` | reads `mars.ini` | Low |
| `Log_management/createlog.py:7-11` | reads `mars.ini` | Low |

Pattern to migrate to:
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_groq_llm(name: str = "70b_versatile") -> ChatGroq:
    return ChatGroq(groq_api_key=get_config("groq_key"), model_name=NAME_TO_MODEL[name], temperature=...)

@lru_cache(maxsize=1)
def get_spacy_lg():
    import spacy
    return spacy.load("en_core_web_lg")
```

---

## Appendix D — Monolithic file inventory

| File | LOC | Suggested split (see [P2-1](#p2-1--monolithic-files) for detail) |
|---|---|---|
| `Ai_module/Query_Classification_And_Analysis.py` | 4,865 | 5–6 modules |
| `Ai_module/Feasibility_Universal_Function/Final_Universal_Function.py` | 1,806 | 3 modules |
| `Ai_module/approval_query/Extraction_for_approval_search.py` | 1,518 | 3 modules (mirror across all four query types) |
| `Ai_module/feasibility_agentic_workflow/feasibility_agent.py` | 1,002 | 4 modules |
| `Management_Class/helpers/utility.py` | 978 | 7 modules |
| `Ai_module/Management_Class/Ai_management/AI.py` | 758 | 2–3 modules |
| `frontend/src/components/ResultScreens/Test/NewIndustryScreen.jsx` | 2,050 | 5+ subcomponents |
| `frontend/src/components/ResultScreens/IndustryResultScreen.jsx` | 1,957 | 5+ subcomponents |
| `frontend/src/components/MapComponent/MapComponent.jsx` | 1,940 | 3 hooks + thin wrapper |
| `frontend/src/components/MapComponent/SingleMap.jsx` | 1,622 | 3 hooks + thin wrapper |
| `frontend/src/components/Chatscreen/Chatscreen.jsx` | 1,476 | 4 subcomponents |

---

## Appendix E — Quick reference: anti-patterns and replacements

| Anti-pattern | Replacement |
|---|---|
| `frappe.db.sql(f"... {x} ...")` | `frappe.db.sql("... %s ...", (x,))` |
| `@frappe.whitelist(allow_guest=True)` on internal logic | `@frappe.whitelist()` + `frappe.has_permission(...)` check |
| `frappe.delete_doc(..., ignore_permissions=True)` | `frappe.only_for("System Manager")` then `frappe.delete_doc(...)` |
| `frappe.db.commit()` mid-handler | Remove; rely on Frappe's automatic commit. |
| Bare `except:` returning fake-success | `except SpecificError as e: frappe.log_error(traceback.format_exc()); return {"error": ...}` |
| Module-level `ChatGroq(...)` | `@lru_cache` factory called on first use |
| Wildcard `from X import *` | Explicit `from X import a, b, c` |
| `key={index}` in mapped lists | `key={item.name}` |
| `<div onClick>` styled as a button | `<button type="button" onClick=...>` |
| Effect with subscription, no cleanup | Return a cleanup function from `useEffect`. |
| Hardcoded path `~/frappe-bench/...` | `frappe.get_app_path("frontend_app", ...)` |

---

*End of review. Next step: confirm Phase 0 scope and assignees.*
