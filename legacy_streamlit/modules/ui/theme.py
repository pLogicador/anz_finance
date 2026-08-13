"""ANZ Finance design system: color tokens, typography and global CSS.

The brand color (#092a55) was sampled from assets/images/logo.png (dominant
non-black pixel color). Everything else in this module is derived from that
anchor to keep a coherent, accessible palette in both dark and light mode.
"""

import streamlit as st

FONT_FAMILY = (
    "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif"
)

# Brand anchors (shared across modes)
BRAND = {
    "navy_900": "#050B16",
    "navy_800": "#092A55",  # sampled from logo
    "navy_700": "#0F3B73",
    "navy_600": "#154E96",
    "accent": "#2F6FED",    # interactive accent derived from the brand hue
    "accent_hover": "#5C8CF2",
    "accent_soft": "rgba(47, 111, 237, 0.14)",
}

SEMANTIC = {
    "success": "#16A34A",
    "success_soft": "rgba(22, 163, 74, 0.14)",
    "warning": "#F59E0B",
    "warning_soft": "rgba(245, 158, 11, 0.14)",
    "danger": "#EF4444",
    "danger_soft": "rgba(239, 68, 68, 0.14)",
    "info": "#38BDF8",
    "info_soft": "rgba(56, 189, 248, 0.14)",
}

# Categorical palette for charts — distinct, colorblind-conscious hues.
CHART_PALETTE = [
    "#2F6FED", "#F59E0B", "#10B981", "#8B5CF6", "#06B6D4",
    "#F43F5E", "#84CC16", "#EC4899", "#FB923C", "#14B8A6", "#94A3B8",
]

# Stable color per known transaction category so charts stay consistent
# across reruns/filters (falls back to CHART_PALETTE cycling for unknowns).
CATEGORY_COLORS = {
    "Moradia": "#2F6FED",
    "Alimentação": "#F59E0B",
    "Mercado": "#10B981",
    "Transporte": "#8B5CF6",
    "Telefone": "#06B6D4",
    "Receitas": "#16A34A",
    "Transferência para terceiros": "#F43F5E",
    "Compras": "#EC4899",
    "Educação": "#FB923C",
    "Saúde": "#14B8A6",
    "Investimento": "#84CC16",
    "Erro na classificação": "#94A3B8",
    "Não classificado": "#64748B",
}


def category_color(name: str, fallback_index: int = 0) -> str:
    if name in CATEGORY_COLORS:
        return CATEGORY_COLORS[name]
    return CHART_PALETTE[fallback_index % len(CHART_PALETTE)]


_DARK_TOKENS = {
    "bg": "#0B0F1A",
    "bg_elevated": "#111726",
    "bg_card": "#141B2E",
    "bg_card_hover": "#182036",
    "bg_sidebar": "#0D1220",
    "bg_input": "#161D30",
    "border": "rgba(255, 255, 255, 0.08)",
    "border_strong": "rgba(255, 255, 255, 0.14)",
    "text_primary": "#E9ECF5",
    "text_secondary": "#9AA4BC",
    "text_muted": "#6B7690",
    "shadow": "0 8px 24px rgba(0, 0, 0, 0.35)",
    "scrollbar": "#26304A",
}

_LIGHT_TOKENS = {
    "bg": "#F6F7FB",
    "bg_elevated": "#FFFFFF",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#F1F4FA",
    "bg_sidebar": "#FFFFFF",
    "bg_input": "#F5F6FA",
    "border": "rgba(15, 23, 42, 0.09)",
    "border_strong": "rgba(15, 23, 42, 0.16)",
    "text_primary": "#0F1729",
    "text_secondary": "#5B6472",
    "text_muted": "#8A93A6",
    "shadow": "0 8px 24px rgba(15, 23, 42, 0.08)",
    "scrollbar": "#D7DCE6",
}


def tokens(mode: str) -> dict:
    base = _DARK_TOKENS if mode == "dark" else _LIGHT_TOKENS
    return {**BRAND, **SEMANTIC, **base}


def plotly_template(mode: str) -> dict:
    """Layout defaults shared by every chart in modules/ui/charts.py."""
    t = tokens(mode)
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, color=t["text_secondary"], size=13),
        # No `title` is ever set on any chart (section_header() provides the
        # heading instead) — setting title_font without title.text made
        # Plotly.js render the literal word "undefined" as a chart title.
        legend=dict(
            font=dict(color=t["text_secondary"], size=12),
            bgcolor="rgba(0,0,0,0)",
        ),
        colorway=CHART_PALETTE,
        height=340,
        margin=dict(l=10, r=10, t=40, b=10),
        hoverlabel=dict(
            bgcolor=t["bg_elevated"],
            bordercolor=t["border_strong"],
            font=dict(family=FONT_FAMILY, color=t["text_primary"]),
        ),
        xaxis=dict(gridcolor=t["border"], zerolinecolor=t["border"], linecolor=t["border"]),
        yaxis=dict(gridcolor=t["border"], zerolinecolor=t["border"], linecolor=t["border"]),
    )


def _css(mode: str) -> str:
    t = tokens(mode)
    return f"""
<style>
:root {{
    --bg: {t['bg']};
    --bg-elevated: {t['bg_elevated']};
    --bg-card: {t['bg_card']};
    --bg-card-hover: {t['bg_card_hover']};
    --bg-sidebar: {t['bg_sidebar']};
    --bg-input: {t['bg_input']};
    --border: {t['border']};
    --border-strong: {t['border_strong']};
    --text-primary: {t['text_primary']};
    --text-secondary: {t['text_secondary']};
    --text-muted: {t['text_muted']};
    --accent: {t['accent']};
    --accent-hover: {t['accent_hover']};
    --accent-soft: {t['accent_soft']};
    --success: {t['success']};
    --success-soft: {t['success_soft']};
    --warning: {t['warning']};
    --warning-soft: {t['warning_soft']};
    --danger: {t['danger']};
    --danger-soft: {t['danger_soft']};
    --info: {t['info']};
    --info-soft: {t['info_soft']};
    --shadow: {t['shadow']};
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --control-height: 2.5rem;
    --font: {FONT_FAMILY};
}}

html, body, [class*="css"] {{
    font-family: var(--font) !important;
}}

/* ---------- App shell ---------- */
[data-testid="stAppViewContainer"] {{
    background: var(--bg);
    color: var(--text-primary);
}}
[data-testid="stHeader"] {{
    background: transparent;
    height: 0;
}}
[data-testid="stToolbar"] {{ right: 1rem; }}
#MainMenu, footer, [data-testid="stDecoration"] {{ visibility: hidden; height: 0; }}

.block-container {{
    padding-top: 1.25rem;
    padding-bottom: 3rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 1280px;
}}

img {{ max-width: 100%; }}
.js-plotly-plot, .plot-container {{ max-width: 100%; }}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {{
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border);
}}
[data-testid="stSidebar"] .block-container {{
    padding-top: 1.5rem;
}}
[data-testid="stSidebarCollapseButton"] button {{
    color: var(--text-secondary);
}}

/* ---------- Typography ---------- */
h1, h2, h3, h4, h5, h6 {{
    color: var(--text-primary) !important;
    font-family: var(--font) !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}}
/* Scoped, not a blanket div/span/p override — that used to flatten every
   secondary/muted/help text in the app (widget captions, uploader hints,
   disabled labels) to full-contrast primary and destroyed hierarchy. */
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{
    color: var(--text-primary);
}}
[data-testid="stWidgetLabel"] p {{
    color: var(--text-secondary);
    font-weight: 500;
    font-size: 0.86rem;
}}
[data-testid="stCaptionContainer"],
[data-testid="stFileUploaderDropzoneInstructions"] small,
.anz-muted {{
    color: var(--text-muted) !important;
}}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
    color: var(--text-secondary) !important;
    font-weight: 500;
    font-size: 0.86rem;
}}

/* ---------- Cards / containers ---------- */
/* Descendant (not direct-child) combinator: the marker sits inside the
   stMarkdown wrapper Streamlit inserts, not directly under stVerticalBlock. */
[data-testid="stVerticalBlockBorderWrapper"]:has(.anz-card-marker) {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow);
    padding: 0.25rem 0.25rem 1rem;
}}
/* Zero-size regardless of Streamlit's (version-dependent) element-wrapper
   markup, so the marker never leaves a visible empty box. */
.anz-card-marker {{ display: block; height: 0; width: 0; margin: 0; padding: 0; overflow: hidden; }}
div[data-testid="stExpander"] {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
}}

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button {{
    background: var(--accent);
    color: #FFFFFF;
    border: none;
    border-radius: var(--radius-sm);
    font-weight: 600;
    font-size: 0.9rem;
    padding: 0.5rem 1.1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.15);
    transition: background 0.15s ease, transform 0.1s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    background: var(--accent-hover);
    transform: translateY(-1px);
}}
.stButton > button:active, .stDownloadButton > button:active {{
    transform: translateY(0);
}}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {{
    outline: 2px solid var(--accent);
    outline-offset: 2px;
}}
button[kind="secondary"] {{
    background: var(--bg-input) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-strong) !important;
}}

/* ---------- Inputs ---------- */
[data-testid="stTextInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stNumberInput"] input,
[data-baseweb="select"] > div {{
    background: var(--bg-input) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}}
[data-testid="stTextInput"] input:focus,
[data-baseweb="select"] > div:focus-within {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
}}
[data-baseweb="tag"] {{
    background: var(--accent) !important;
    border-radius: 6px !important;
}}

/* ---------- File uploader ---------- */
[data-testid="stFileUploaderDropzone"] {{
    background: var(--bg-input);
    border: 1.5px dashed var(--border-strong);
    border-radius: var(--radius-md);
}}
[data-testid="stFileUploaderDropzone"]:hover {{
    border-color: var(--accent);
}}

/* ---------- Tabs ---------- */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid var(--border);
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 0.88rem;
    padding: 0.6rem 0.9rem;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}}

/* ---------- DataFrame / table ---------- */
[data-testid="stDataFrame"] {{
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    overflow: hidden;
}}

/* ---------- Status / alerts ---------- */
/* Streamlit's alert/status colors come from the static .streamlit/config.toml
   theme (always dark) — without this override, switching to light mode here
   would leave alerts rendered in dark-theme colors on a light background. */
div[data-testid="stAlertContainer"] {{
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
    background: var(--bg-input);
}}
div[data-testid="stAlertContainer"] p {{ color: var(--text-primary) !important; }}
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {{
    background: var(--info-soft); border-color: var(--info);
}}
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {{
    background: var(--success-soft); border-color: var(--success);
}}
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {{
    background: var(--warning-soft); border-color: var(--warning);
}}
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {{
    background: var(--danger-soft); border-color: var(--danger);
}}

[data-testid="stStatusWidget"] {{
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
    background: var(--bg-card);
}}
div[data-testid="stExpander"] summary, div[data-testid="stExpander"] p {{
    color: var(--text-primary) !important;
}}

/* ---------- Dropdown popovers (select / multiselect menus) ---------- */
/* BaseWeb renders these in a portal outside the normal component tree, so
   the input/label rules above never reach them — left unstyled they show
   BaseWeb's own default light/dark colors regardless of our toggle. */
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] ul {{
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-strong) !important;
}}
[data-baseweb="popover"] li {{ color: var(--text-primary) !important; }}
[data-baseweb="popover"] li:hover {{ background: var(--bg-card-hover) !important; }}

/* ---------- Scrollbars ---------- */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--scrollbar); border-radius: 8px; }}

/* ---------- Misc ---------- */
hr {{ border-color: var(--border); }}
[data-testid="stMetricValue"] {{ color: var(--text-primary); }}

/* ---------- Custom component classes (see components.py) ---------- */
.anz-topbar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.85rem 0; margin-bottom: 1.25rem;
    border-bottom: 1px solid var(--border);
}}
.anz-topbar-brand {{ display: flex; align-items: center; gap: 0.65rem; }}
.anz-topbar-title {{ font-weight: 800; font-size: 1.05rem; color: var(--text-primary); letter-spacing: -0.01em; }}
.anz-topbar-subtitle {{ font-size: 0.78rem; color: var(--text-muted); }}
.anz-user-chip {{
    display: flex; align-items: center; gap: 0.5rem;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 999px; padding: 0.35rem 0.85rem 0.35rem 0.4rem;
    font-size: 0.82rem; color: var(--text-secondary);
}}
.anz-user-avatar {{
    width: 24px; height: 24px; border-radius: 50%;
    background: var(--accent); color: #fff; display: flex;
    align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700;
}}

.anz-kpi-card {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--radius-lg); padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow); height: 100%;
    display: flex; flex-direction: column;
}}
.anz-kpi-head {{
    display: flex; align-items: flex-start; justify-content: space-between; gap: 0.75rem;
}}
.anz-kpi-label {{
    font-size: 0.78rem; color: var(--text-muted); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.04em; line-height: 1.3;
}}
.anz-kpi-value {{
    font-size: 1.5rem; font-weight: 800; color: var(--text-primary);
    margin-top: 0.35rem; letter-spacing: -0.02em; line-height: 1.25;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}}
.anz-kpi-footnote {{ font-size: 0.78rem; color: var(--text-muted); margin-top: 0.2rem; }}
.anz-kpi-delta {{ display: inline-flex; align-items: center; gap: 0.25rem; margin-top: auto; padding-top: 0.5rem; font-size: 0.8rem; font-weight: 600; }}
.anz-kpi-delta .pill {{ padding: 0.15rem 0.5rem; border-radius: 999px; }}
.anz-kpi-delta.up .pill {{ color: var(--success); background: var(--success-soft); }}
.anz-kpi-delta.down .pill {{ color: var(--danger); background: var(--danger-soft); }}
.anz-kpi-delta.flat .pill {{ color: var(--text-muted); background: var(--bg-input); }}
.anz-kpi-icon {{
    flex: 0 0 auto; width: 34px; height: 34px; border-radius: 10px; display: flex;
    align-items: center; justify-content: center; font-size: 1rem;
    background: var(--accent-soft);
}}

.anz-section-title {{ font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin: 0 0 0.75rem; }}
.anz-section-subtitle {{ font-size: 0.82rem; color: var(--text-muted); margin-top: 0.15rem; }}

.anz-sidebar-heading {{
    font-size: 0.72rem; font-weight: 700; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.06em;
    margin: 0 0 0.6rem;
}}

.anz-table-nav-label {{
    display: flex; align-items: center; justify-content: center;
    height: var(--control-height); color: var(--text-muted); font-size: 0.82rem;
}}

.anz-badge {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    font-size: 0.74rem; font-weight: 600; padding: 0.2rem 0.55rem;
    border-radius: 999px; white-space: nowrap;
}}
.anz-badge.positive {{ color: var(--success); background: var(--success-soft); }}
.anz-badge.negative {{ color: var(--danger); background: var(--danger-soft); }}
.anz-badge.neutral {{ color: var(--text-secondary); background: var(--bg-input); }}

.anz-empty-state {{
    text-align: center; padding: 3rem 1.5rem; color: var(--text-muted);
    background: var(--bg-card); border: 1px dashed var(--border-strong);
    border-radius: var(--radius-lg);
}}
.anz-empty-state .icon {{ font-size: 2.2rem; margin-bottom: 0.75rem; }}
.anz-empty-state .title {{ font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.25rem; }}

.anz-divider {{ height: 1px; background: var(--border); margin: 1.5rem 0; border: none; }}

/* ---------- Responsive breakpoints ---------- */
/* Tabs can overflow their container at narrow widths (e.g. a 4-tab row in
   a ~480px-wide content area next to the sidebar on tablet) — scroll them
   horizontally instead of silently clipping the last tab off-screen. */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    overflow-x: auto; flex-wrap: nowrap; scrollbar-width: thin;
}}

@media (max-width: 992px) {{
    .block-container {{ padding-left: 1.25rem; padding-right: 1.25rem; }}

    /* Between the phone breakpoint below (full stack) and desktop: wrap
       st.columns() rows into a 2-per-row grid instead of squeezing 4 KPI
       cards (or 2 charts) into a sidebar-shrunk ~480px content area, which
       was truncating KPI values down to an unreadable "R$...". */
    [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; row-gap: 0.75rem; }}
    [data-testid="stColumn"] {{ min-width: 45% !important; flex: 1 1 45% !important; }}
}}

@media (max-width: 640px) {{
    .block-container {{ padding-left: 0.75rem; padding-right: 0.75rem; padding-top: 0.75rem; }}

    /* Force every st.columns() row (KPIs, chart pairs, table search/page-size,
       table pagination controls) to stack full-width instead of squeezing
       side by side — the single biggest cause of overflow/illegibility on phones. */
    [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; row-gap: 0.75rem; }}
    [data-testid="stColumn"] {{ min-width: 100% !important; width: 100% !important; flex: 1 1 100% !important; }}

    .anz-topbar {{ flex-wrap: wrap; row-gap: 0.6rem; padding: 0.6rem 0; }}
    .anz-topbar-subtitle {{ display: none; }}
    .anz-user-chip span {{ display: none; }}
    .anz-user-chip {{ padding: 0.3rem; }}

    .anz-kpi-card {{ padding: 0.85rem 1rem; }}
    .anz-kpi-value {{ font-size: 1.25rem; }}
    .anz-kpi-label {{ font-size: 0.72rem; }}

    .anz-section-title {{ font-size: 0.95rem; }}

    .anz-empty-state {{ padding: 2rem 1rem; }}
    .anz-empty-state .icon {{ font-size: 1.8rem; }}

    [data-testid="stTabs"] [data-baseweb="tab"] {{ padding: 0.5rem 0.55rem; font-size: 0.8rem; }}
}}
</style>
"""


def apply(mode: str = "dark") -> None:
    st.markdown(_css(mode), unsafe_allow_html=True)
