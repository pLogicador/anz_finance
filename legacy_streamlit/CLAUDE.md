# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

ANZ Finance parses OFX bank statements, classifies each transaction into a financial category using a Groq LLM (via LangChain), and shows the results in a Streamlit dashboard with KPIs, filters, a modernized table, and Plotly charts styled by a custom design system (`modules/ui/`) so the app doesn't look like default Streamlit. README.md is in Portuguese; keep user-facing strings and commit context in Portuguese unless told otherwise.

## Setup and commands

Dependencies are declared in both `pyproject.toml` (Poetry, Python ">=3.12,<4.0") and `requirements.txt` (pip freeze snapshot). Prefer Poetry when adding/removing dependencies so `pyproject.toml` stays authoritative, but installs may go through either file depending on the environment.

```bash
poetry install                 # or: pip install -r requirements.txt
```

Required environment variables (loaded from `.env` via `config.py`):
- `GROQ_API_KEY` — used by `modules/llm/categorizer.py` to call Groq models.
- `API_BASE`, `API_HUB` — used only by `run_dashboard.py` for its external token-auth check.

Run the CLI pipeline (parses `extratos/*.ofx` → classifies → writes `finances.csv`):
```bash
python generate_csv.py
```

Run the Streamlit dashboard:
```bash
streamlit run run_dashboard.py
```
Note: `run_dashboard.py` gates access behind an external token-validation API (`API_BASE/validate-agendador-token`), read from a `?token=` query param. This app is one piece of a larger platform ("Syncron"): login happens in a *separate* Syncron frontend/API (not in this repo), which redirects here with `?token=...` already issued — `run_dashboard.py` only *validates* that token via `validate_token_with_api()`, it never issues or manages tokens itself. Without a valid token (and reachable `API_BASE`/`API_HUB`), the dashboard shows a styled login wall (`_render_login_wall` in `run_dashboard.py`) and stops. For local dashboard iteration on `run_finance_dashboard()` itself, it's often easier to call `modules.dashboard.streamlit_app.run_finance_dashboard()` directly from a throwaway `streamlit run` entrypoint to bypass the auth wall — the auth logic itself (`validate_token_with_api`, `get_token_from_query`) is intentionally untouched by the UI layer and shouldn't be bypassed in real usage.

There is no test suite, lint config, or CI in this repo currently. `ruff` is available (`python -m ruff check modules run_dashboard.py generate_csv.py --select F,E9`) but not wired into any hook/CI. `streamlit.testing.v1.AppTest` can be used for in-process smoke checks of render functions (it does not support simulating `st.file_uploader`, so drive internal functions like `_render_dashboard(df, mode)` directly with a synthetic DataFrame instead) — but AppTest only proves the Python side doesn't raise; it does **not** catch how the browser actually renders the HTML/JS (see the "undefined" and "raw HTML leaking" gotchas below, neither of which AppTest could have caught).

**Visually verifying changes in this sandboxed dev environment:** headless Chrome's `--screenshot --virtual-time-budget=N` does *not* work against this app — Streamlit's WebSocket-driven rerender never gets delivered under Chrome's deterministic virtual clock, so the screenshot captures a frozen loading skeleton no matter how large `N` is (confirmed up to 90s, on pages as trivial as "hello world" + two tabs). What does work: launch headless Chrome with `--remote-debugging-port`, drive it over the raw DevTools Protocol (`Page.navigate` → real `Start-Sleep`/`sleep` of several real seconds → `Page.captureScreenshot`), i.e. a genuine wall-clock wait instead of virtual time. No Playwright/puppeteer is installed; a ~70-line PowerShell script using `System.Net.WebSockets.ClientWebSocket` against the CDP JSON endpoint is enough (add a `Runtime.evaluate` call with a `document.querySelector(...).click()` expression between navigate and screenshot to drive tab clicks, the theme toggle, etc.). Always launch with a fresh `--user-data-dir` and kill only that specific PID afterward — never broadly `Stop-Process -Name chrome`, which will also kill the user's real browser windows.

## Architecture

Data flows through four stages, mirrored in both the CLI (`generate_csv.py`) and the dashboard (`modules/dashboard/streamlit_app.py::run_finance_dashboard`), which independently reimplement the same pipeline against different input sources:

1. **Parse** (`modules/parsers/ofx_parser.py`) — reads OFX files into a DataFrame with columns `Data`, `Valor`, `Descrição`, `ID`, via a shared `_extract_transactions()` helper.
   - `parse_ofx_files_from_upload(files)` — used by the dashboard, takes Streamlit `UploadedFile` objects.
   - `parse_ofx_files(folder)` — used by the CLI, globs `*.ofx` in `folder` (i.e. `extratos/`, gitignored).
2. **Preprocess** (`modules/data/finance_data.py::preprocess_df`) — drops `ID`, converts `Data` to datetime then back to date, and derives a `Mês` (month) column as `YYYY-MM` for filtering.
3. **Classify** (`modules/llm/categorizer.py::Categorizer`) — sends each transaction description through a Portuguese prompt template to a Groq chat model (default `llama-3.1-8b-instant`, falling back to `llama-3.1-70b-versatile` on init failure), returning one of a fixed set of category labels (Moradia, Alimentação, Mercado, Transporte, Telefone, Receitas, Transferência para terceiros, Compras, Educação, Saúde, Investimento) — or `"Error"` if the API call itself fails. Classification is done one description at a time in a loop (no batching), so large statements are slow and make many API calls. **Do not change this file, its prompt, or its category set** — the UI layer keys off these exact labels for chart coloring (`modules/ui/theme.py::CATEGORY_COLORS`). Immediately after calling `classify()`, `streamlit_app.py::_get_or_process` normalizes the result for *display only* (blank/whitespace/NaN → `"Não classificado"`, `"Error"` → `"Erro na classificação"`) — this doesn't change what the classifier returns, only how an edge-case result is labeled before it reaches any chart/table/filter. Don't remove this: an unnormalized blank category renders as a broken/invisible legend entry.
4. **Present/Filter** (`modules/data/finance_data.py::filter_transactions`, `modules/dashboard/streamlit_app.py`) — `filter_transactions(df, month, categories)` is the one business-logic filter function; an empty `categories` list means "no filter", not "show nothing" — any additive filtering (type, search, year) done in the UI layer must preserve that semantic (see `_apply_type_filter` in `streamlit_app.py`).

`config.py` centralizes env/config loading (`GROQ_API_KEY`, `DATA_FOLDER="extratos"`, `OUTPUT_CSV="finances.csv"`) and is imported by both the CLI and LLM modules.

`extratos/` (input OFX files) and `*.csv` (generated output) are gitignored — never expect them to be present in a fresh checkout.

## UI / design system (`modules/ui/`)

The dashboard's visual layer is deliberately isolated from business logic so the Groq/OFX/data pipeline can be touched independently of styling. `.streamlit/config.toml` sets a static dark base theme (chrome shown before the CSS below loads); the actual dark/light experience is driven at runtime by the modules below.

- **`theme.py`** — color tokens (dark + light), typography, a shared `plotly_template(mode)`/`CHART_PALETTE`/`category_color()`, and one big CSS block (`apply(mode)`) that reskins Streamlit's native DOM via `data-testid` selectors, including a responsive breakpoint system (see below). Brand color (`#092a55`) was sampled from `assets/images/logo.png`; `CATEGORY_COLORS` maps the categorizer's fixed labels (plus the two normalized fallback labels above) to stable chart colors. Mode (dark/light) is plain server-side state (`st.session_state["anz_mode"]`) — there's no client-side toggle; switching reruns the script and re-emits CSS for the new mode. Don't reintroduce the Google Fonts `@import` that used to be here — it caused the app to hang waiting on an external font fetch in network-restricted environments; the CSS relies on the system-font fallback stack in `FONT_FAMILY` instead. Alert boxes (`st.info`/`st.error`/etc.) and BaseWeb dropdown popovers are *explicitly* recolored with our tokens — they don't naturally follow the runtime mode toggle since `config.toml`'s `[theme]` is static, so without this override they'd render in dark-theme colors even when the page is in light mode.
- **`components.py`** — reusable widgets: `topbar`, `kpi_card`/`kpi_row` (with an `invert` flag for "more is bad" metrics and an optional `footnote` slot for label/value pairs like top category), `section_header`, `sidebar_heading`, `badge`, `empty_state`, `card()` (a `contextmanager` wrapping `st.container(border=True)` — every chart panel and the table live inside one), `transactions_table` (search/sort/pagination/export). Pure presentation; never imports from `modules/llm` or `modules/data`.
- **`metrics.py`** — read-only aggregations (`summarize`, `monthly_series`, `category_breakdown`, `month_over_month_delta`) computed on top of the already-classified DataFrame. Note `month_over_month_delta(..., "expense")` returns delta on the raw (negative) expense sum — callers wanting "positive = spent more" must negate it (see `_render_kpis` in `streamlit_app.py` for the `invert=True` pattern used to keep KPI-card coloring correct for metrics where "more" is bad).
- **`charts.py`** — themed Plotly figure builders (donut, monthly bar, cumulative area, top-categories bar, category×month heatmap), all sharing `theme.plotly_template(mode)` via the local `_apply_layout()` helper (which does a one-level-deep dict merge, not a flat `.update()`, so e.g. overriding just `legend.orientation` doesn't blow away the base theme's `legend.font`).

`modules/dashboard/streamlit_app.py::_get_or_process` caches the parsed+classified DataFrame in `st.session_state` keyed by `(filename, size)` per uploaded file. This matters: Streamlit reruns the whole script on every widget interaction (filter change, pagination click, theme toggle), so without this cache every click would silently re-run OFX parsing and re-call the Groq classifier from scratch.

### Gotchas found the hard way (don't reintroduce these)

- **A markdown line that's only `{some_var}` breaks if that variable can be `""`.** Streamlit/CommonMark treats a raw HTML block starting with a generic tag (`<div>`, not `<style>`/`<script>`/`<pre>`) as ending at the first *blank* line. A multi-line f-string like `f"...<div>{value}</div>\n{maybe_empty}\n</div>"` goes blank exactly when `maybe_empty == ""`, and everything after gets misparsed as an indented code block — it renders as literal escaped HTML text on screen (this is exactly what caused the KPI cards to show raw `<div class="anz-kpi-de...` text in production). `kpi_card()` and `topbar()` in `components.py` are written as single-line HTML strings specifically to make this impossible — keep that pattern for any new multi-piece HTML component, or guarantee every optional line still has literal non-empty tag content around it (see `empty_state()`'s `subtitle` line for that safer alternative).
- **Never set `title_font` in `plotly_template()` without a chart also setting `title`.** No chart here sets a Plotly-native title (chart titles come from `section_header()` markdown above the chart instead) — `title_font` alone with no `title.text` makes Plotly.js render the literal word "undefined" as the chart's title. If you ever add a chart-native title, set both together.
- **Month-string x-axes need `xaxis=dict(type="category")`.** Plotly auto-detects axis type from the data; a `"Mês"` column of `"YYYY-MM"` strings gets silently (mis)treated as a date axis otherwise, producing nonsense tick labels like "Jan 29" instead of "2026-02". All three by-month charts (`monthly_income_vs_expense`, `cumulative_balance`, `category_month_heatmap`) set this explicitly.
- **`st.column_config.NumberColumn(format=...)` can't produce Brazilian `"1.234,56"`** — its format string is Python/printf-style (period decimal) only. `transactions_table()`'s `Valor` column is pre-formatted as text via the same `format_currency()` helper the KPI cards use, specifically to keep currency formatting consistent app-wide (this trades away native numeric column-sort for that column).
- **Responsive breakpoints in `theme.py`**: `@media (max-width: 992px)` wraps every `st.columns()` row into a 2-per-row grid (`[data-testid="stColumn"] { flex: 1 1 45% }`); `@media (max-width: 640px)` (declared after, so it wins at the narrowest widths) forces full single-column stacking instead. Without the 992px tier, the gap between it and 640px let a 4-card KPI row get squeezed down to unreadable `"R$..."` truncation on real tablet widths (~834px) — if you add new multi-column layouts, test at ~834px specifically, not just desktop and phone.
