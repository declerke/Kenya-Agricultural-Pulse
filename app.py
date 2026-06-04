"""
Kenya Agricultural Pulse — Streamlit BI Dashboard
Story: Kenya's food basket — production trends, food security,
and agricultural transformation 2000–2024.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import io

# ──────────────────────────────────────────────────────────────
# PAGE CONFIG (must be first Streamlit call)
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kenya Agricultural Pulse",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# CUSTOM CSS — dark BI theme
# ──────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"] { display: none !important; }
span.material-symbols-rounded,
span.material-symbols-outlined,
span.material-icons { visibility: hidden !important; font-size: 0 !important; }

/* Background */
.stApp { background-color: #060b17; }
.block-container { padding-top: 2rem; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0a0f1e;
    border-right: 1px solid rgba(0,210,106,0.12);
}
[data-testid="stSidebar"] .stMarkdown p { color: #a0aec0; font-size: 0.85rem; }

/* KPI metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0f1729 0%, #1a2744 100%);
    border: 1px solid rgba(0,210,106,0.15);
    border-radius: 12px;
    padding: 1rem 1.25rem !important;
    border-left: 3px solid #00d26a;
}
[data-testid="metric-container"] label { color: #718096 !important; font-size: 0.8rem !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #e2e8f0 !important; font-size: 1.6rem !important; }
[data-testid="stMetricDelta"] svg { display: none; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0f1729;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(0,210,106,0.1);
}
.stTabs [data-baseweb="tab"] {
    color: #718096;
    border-radius: 7px;
    font-weight: 500;
    font-size: 0.875rem;
    padding: 0.4rem 1rem;
}
.stTabs [aria-selected="true"] {
    background: #00d26a !important;
    color: #000 !important;
    font-weight: 600 !important;
}

/* Typography */
h1 { color: #e2e8f0 !important; font-weight: 700 !important; letter-spacing: -0.5px; }
h2 { color: #cbd5e0 !important; font-size: 1.15rem !important; font-weight: 600 !important; }
h3 { color: #a0aec0 !important; font-size: 1rem !important; }
p  { color: #cbd5e0; }

/* Insight callout boxes */
.insight-box {
    background: linear-gradient(135deg, #0f1729 0%, #1c2a44 100%);
    border-left: 4px solid #f5a623;
    border-radius: 8px;
    padding: 0.9rem 1.4rem;
    margin: 1rem 0;
    color: #e2e8f0;
    font-size: 0.92rem;
    line-height: 1.6;
}
.insight-box strong { color: #f5a623; }

.alert-good {
    background: linear-gradient(135deg, #0a1f12 0%, #0d2918 100%);
    border-left: 4px solid #00d26a;
    border-radius: 8px;
    padding: 0.9rem 1.4rem;
    margin: 1rem 0;
    color: #e2e8f0;
    font-size: 0.92rem;
}

/* Dividers */
hr { border-color: rgba(0,210,106,0.1) !important; }

/* Data table */
.stDataFrame { border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; }

/* Multiselect tags */
[data-baseweb="tag"] { background: rgba(0,210,106,0.15) !important; }

/* Plotly chart containers */
.js-plotly-plot .plotly { border-radius: 10px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# CHART THEME HELPERS
# ──────────────────────────────────────────────────────────────
PALETTE = ['#00d26a', '#f5a623', '#4299e1', '#ce1126', '#9f7aea', '#38b2ac', '#ed64a6']
COUNTRY_COLORS = {
    'KE': '#00d26a',
    'UG': '#f5a623',
    'TZ': '#4299e1',
    'ET': '#9f7aea',
    'NG': '#ed64a6',
}
COUNTRY_NAMES = {
    'KE': 'Kenya', 'UG': 'Uganda', 'TZ': 'Tanzania', 'ET': 'Ethiopia', 'NG': 'Nigeria',
}
COUNTRY_NAMES_INV = {v: k for k, v in COUNTRY_NAMES.items()}


def lerp_color(t: float) -> str:
    """Interpolate red→amber→green for a normalised value t in [0, 1]."""
    if t < 0.5:
        r, g, b = 220, int(80 + t * 2 * 165), 50
    else:
        r, g, b = int(220 - (t - 0.5) * 2 * 180), 210, 50
    return f'rgb({r},{g},{b})'


def chart_layout(title: str = "", height: int = 420, y_title: str = "", x_title: str = "") -> dict:
    return dict(
        title=dict(text=title, font=dict(color='#e2e8f0', size=15, family='Inter'), x=0.01),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(11,18,40,0.6)',
        font=dict(color='#a0aec0', family='Inter', size=12),
        height=height,
        margin=dict(l=10, r=10, t=52, b=10),
        xaxis=dict(
            title=dict(text=x_title, font=dict(color='#718096', size=11)),
            gridcolor='rgba(255,255,255,0.04)',
            linecolor='rgba(255,255,255,0.08)',
            zeroline=False,
            tickfont=dict(color='#718096'),
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(color='#718096', size=11)),
            gridcolor='rgba(255,255,255,0.04)',
            linecolor='rgba(255,255,255,0.08)',
            zeroline=False,
            tickfont=dict(color='#718096'),
        ),
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='#a0aec0', size=11),
            bordercolor='rgba(255,255,255,0.06)',
            borderwidth=1,
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='#1a2744',
            bordercolor='rgba(0,210,106,0.3)',
            font=dict(color='#e2e8f0', family='Inter', size=12),
        ),
    )


def insight(text: str, variant: str = "warning"):
    css_class = "insight-box" if variant == "warning" else "alert-good"
    st.markdown(f'<div class="{css_class}">{text}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return pd.read_parquet('data/processed/agri.parquet')


try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "Data not found. Run `python data_pipeline.py` first to fetch the World Bank data.",
        icon="🚨",
    )
    st.stop()

# Convenience: Kenya-only slice
ALL_COLS = df.columns.tolist()


# ──────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌾 Kenya Agri Pulse")
    st.markdown("*Food security & agricultural transformation 2000–2024*")
    st.markdown("---")

    year_range = st.slider("Year Range", 2000, 2024, (2003, 2024))

    st.markdown("---")
    st.markdown("### Compare Countries")
    peer_options = {'Uganda': 'UG', 'Tanzania': 'TZ', 'Ethiopia': 'ET', 'Nigeria': 'NG'}
    selected_peers = st.multiselect(
        "East African Peers",
        list(peer_options.keys()),
        default=['Uganda', 'Tanzania', 'Ethiopia'],
    )
    selected_codes = ['KE'] + [peer_options[p] for p in selected_peers]

    st.markdown("---")
    st.markdown(
        "**Source:** [World Bank WDI](https://databank.worldbank.org/source/world-development-indicators)\n\n"
        "**Coverage:** 2000–2024 · 5 countries\n\n"
        "**Last updated:** Pipeline fetches live data"
    )


# ──────────────────────────────────────────────────────────────
# FILTER DATA
# ──────────────────────────────────────────────────────────────
dff = df[df['year'].between(year_range[0], year_range[1])].copy()
ke_f = dff[dff['economy'] == 'KE'].copy()
ke_all = df[df['economy'] == 'KE'].copy()  # unfiltered for KPIs
comp_f = dff[dff['economy'].isin(selected_codes)].copy()


# ──────────────────────────────────────────────────────────────
# HELPER: latest non-null value + delta
# ──────────────────────────────────────────────────────────────
def latest_val(series: pd.Series, years: pd.Series, lookback: int = 10):
    """Return (latest_value, latest_year, delta_vs_N_years_ago)."""
    valid = pd.DataFrame({'val': series.values, 'yr': years.values}).dropna()
    if valid.empty:
        return None, None, None
    latest_row = valid.loc[valid['yr'].idxmax()]
    lval, lyr = latest_row['val'], int(latest_row['yr'])
    target_yr = lyr - lookback
    prior = valid[valid['yr'] <= target_yr]
    if prior.empty:
        delta = None
    else:
        prior_row = prior.loc[prior['yr'].idxmax()]
        delta = lval - prior_row['val']
    return lval, lyr, delta


# ──────────────────────────────────────────────────────────────
# HERO HEADER
# ──────────────────────────────────────────────────────────────
st.markdown(
    "# 🌾 Kenya Agricultural Pulse",
)
st.markdown(
    "**Kenya's food basket — production trends, food security, and agricultural transformation 2000–2024.**  "
    "Data: World Bank World Development Indicators."
)
st.markdown("---")

# ──────────────────────────────────────────────────────────────
# KPI CARDS
# ──────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# KPI 1 — Food Production Index
if 'Food Production Index' in ke_all.columns:
    fpi_val, fpi_yr, fpi_delta = latest_val(ke_all['Food Production Index'], ke_all['year'])
    with kpi1:
        delta_str = f"{fpi_delta:+.1f} pts (10yr)" if fpi_delta is not None else "—"
        st.metric(
            "Food Production Index",
            f"{fpi_val:.1f}" if fpi_val else "—",
            delta=delta_str,
        )
else:
    with kpi1:
        st.metric("Food Production Index", "—", delta="No data")

# KPI 2 — Cereal Yield
if 'Cereal Yield (kg/ha)' in ke_all.columns:
    cy_val, cy_yr, cy_delta = latest_val(ke_all['Cereal Yield (kg/ha)'], ke_all['year'])
    with kpi2:
        delta_str = f"{cy_delta:+.0f} kg/ha (10yr)" if cy_delta is not None else "—"
        st.metric(
            "Cereal Yield",
            f"{cy_val:,.0f} kg/ha" if cy_val else "—",
            delta=delta_str,
        )
else:
    with kpi2:
        st.metric("Cereal Yield", "—", delta="No data")

# KPI 3 — Undernourishment Rate (lower is better)
if 'Undernourishment Rate (%)' in ke_all.columns:
    un_val, un_yr, un_delta = latest_val(ke_all['Undernourishment Rate (%)'], ke_all['year'])
    with kpi3:
        # Negative delta = improvement
        delta_str = f"{un_delta:+.1f} pp (10yr)" if un_delta is not None else "—"
        st.metric(
            "Undernourishment Rate",
            f"{un_val:.1f}%" if un_val else "—",
            delta=delta_str,
            delta_color="inverse",
        )
else:
    with kpi3:
        st.metric("Undernourishment Rate", "—", delta="No data")

# KPI 4 — Agriculture % GDP
if 'Agriculture % GDP' in ke_all.columns:
    agdp_val, agdp_yr, agdp_delta = latest_val(ke_all['Agriculture % GDP'], ke_all['year'])
    with kpi4:
        delta_str = f"{agdp_delta:+.1f} pp (10yr)" if agdp_delta is not None else "—"
        st.metric(
            "Agriculture % of GDP",
            f"{agdp_val:.1f}%" if agdp_val else "—",
            delta=delta_str,
        )
else:
    with kpi4:
        st.metric("Agriculture % of GDP", "—", delta="No data")

st.markdown("---")

# ──────────────────────────────────────────────────────────────
# EXECUTIVE SUMMARY BANNER
# ──────────────────────────────────────────────────────────────
_ag_emp_rows = ke_all[ke_all['Agricultural Employment %'].notna()].sort_values('year')
_ag_gdp_rows = ke_all[ke_all['Agriculture % GDP'].notna()].sort_values('year')
_undernut_rows = ke_all[ke_all['Undernourishment Rate (%)'].notna()].sort_values('year')
_food_idx_rows = ke_all[ke_all['Food Production Index'].notna()].sort_values('year')

if not _ag_emp_rows.empty and not _ag_gdp_rows.empty and not _undernut_rows.empty and not _food_idx_rows.empty:
    _ag_emp = _ag_emp_rows.iloc[-1]
    _ag_gdp = _ag_gdp_rows.iloc[-1]
    _undernut = _undernut_rows.iloc[-1]
    _food_idx = _food_idx_rows.iloc[-1]
    _productivity_gap = _ag_emp['Agricultural Employment %'] - _ag_gdp['Agriculture % GDP']

    exec_text = f"""
<div style="background:linear-gradient(135deg,#0f1729,#1a2744);border-radius:12px;padding:1.2rem 1.5rem;border:1px solid rgba(0,210,106,0.2);margin-bottom:1.5rem">
<div style="color:#00d26a;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;margin-bottom:0.6rem">&#x1F4CB; KEY FINDINGS</div>
<ul style="color:#cbd5e0;margin:0;padding-left:1.2rem;line-height:1.8">
<li><strong style="color:#f5a623">Productivity Crisis:</strong> Agriculture employs <strong>{_ag_emp['Agricultural Employment %']:.1f}%</strong> of Kenya's workforce but contributes only <strong>{_ag_gdp['Agriculture % GDP']:.1f}%</strong> of GDP — a <strong style="color:#ce1126">{_productivity_gap:.1f}pp productivity gap</strong> signaling low agricultural value per worker.</li>
<li><strong style="color:#f5a623">Food Security:</strong> <strong style="color:#ce1126">{_undernut['Undernourishment Rate (%)']:.1f}%</strong> of Kenya's population faces undernourishment — nearly 1 in 3 Kenyans ({int(_undernut['year'])}).</li>
<li>Food production index stands at <strong style="color:#00d26a">{_food_idx['Food Production Index']:.1f}</strong> (baseline: 2014–2016 = 100), showing steady improvement since 2000.</li>
<li>Agricultural transformation is underway but slow — rural-to-urban migration and yield improvements are needed to close the productivity gap.</li>
</ul>
</div>
"""
    st.markdown(exec_text, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Production & Yields",
    "🍽️ Food Security",
    "🔄 Structural Transformation",
    "📥 Export Data",
])


# ══════════════════════════════════════════════════════════════
# TAB 1 — Production & Yields
# ══════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Production Indices & Yield Trends")

    # ── Chart 1: Food + Livestock Production Index ─────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Food vs Livestock Production Index — Kenya")
        fig = go.Figure()

        if 'Food Production Index' in ke_f.columns:
            fig.add_trace(go.Scatter(
                x=ke_f['year'], y=ke_f['Food Production Index'],
                name='Food Production',
                line=dict(color='#00d26a', width=2.5),
                fill='tozeroy',
                fillcolor='rgba(0,210,106,0.06)',
                mode='lines+markers',
                marker=dict(size=4),
            ))

        if 'Livestock Production Index' in ke_f.columns:
            fig.add_trace(go.Scatter(
                x=ke_f['year'], y=ke_f['Livestock Production Index'],
                name='Livestock Production',
                line=dict(color='#f5a623', width=2.5, dash='dot'),
                mode='lines+markers',
                marker=dict(size=4),
            ))

        # Annotate notable events
        for yr, label_text, color in [
            (2009, "2009 Drought", '#ce1126'),
            (2011, "East Africa Drought", '#ce1126'),
            (2017, "Drought Year", '#ce1126'),
            (2020, "COVID Supply Disruptions", '#f5a623'),
        ]:
            if year_range[0] <= yr <= year_range[1]:
                fig.add_vline(
                    x=yr,
                    line=dict(color=color, width=1, dash='dash'),
                    annotation=dict(
                        text=label_text,
                        font=dict(color=color, size=10),
                        textangle=-90,
                        yanchor='top',
                    ),
                )

        layout = chart_layout(y_title="Index (2014–2016 = 100)", height=400)
        layout['xaxis']['dtick'] = 4
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    # ── Chart 2: Cereal Yield comparison ───────────────────────
    with col_b:
        st.markdown("#### Cereal Yield — Kenya vs Peers (kg/ha)")
        fig2 = go.Figure()

        if 'Cereal Yield (kg/ha)' in comp_f.columns:
            for eco in selected_codes:
                sub = comp_f[comp_f['economy'] == eco]
                valid = sub.dropna(subset=['Cereal Yield (kg/ha)'])
                if valid.empty:
                    continue
                is_ke = eco == 'KE'
                fig2.add_trace(go.Scatter(
                    x=valid['year'],
                    y=valid['Cereal Yield (kg/ha)'],
                    name=COUNTRY_NAMES.get(eco, eco),
                    line=dict(
                        color=COUNTRY_COLORS.get(eco, '#a0aec0'),
                        width=3 if is_ke else 1.5,
                    ),
                    mode='lines',
                    opacity=1.0 if is_ke else 0.7,
                ))

            # Kenya fill
            ke_cy = comp_f[comp_f['economy'] == 'KE'].dropna(subset=['Cereal Yield (kg/ha)'])
            if not ke_cy.empty:
                fig2.add_trace(go.Scatter(
                    x=ke_cy['year'],
                    y=ke_cy['Cereal Yield (kg/ha)'],
                    fill='tozeroy',
                    fillcolor='rgba(0,210,106,0.05)',
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo='skip',
                ))

        layout2 = chart_layout(y_title="kg per hectare", height=400)
        layout2['xaxis']['dtick'] = 4
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Chart 3: Fertilizer Consumption ────────────────────────
    st.markdown("#### Fertilizer Consumption — Kenya (kg per hectare of arable land)")
    if 'Fertilizer Consumption (kg/ha)' in ke_f.columns:
        fe_data = ke_f.dropna(subset=['Fertilizer Consumption (kg/ha)']).copy()
        # Color scale: low = red, high = green
        fe_min = fe_data['Fertilizer Consumption (kg/ha)'].min()
        fe_max = fe_data['Fertilizer Consumption (kg/ha)'].max()
        fe_norm = (fe_data['Fertilizer Consumption (kg/ha)'] - fe_min) / (fe_max - fe_min + 1e-9)

        bar_colors = [lerp_color(t) for t in fe_norm]
        fig3 = go.Figure(go.Bar(
            x=fe_data['year'],
            y=fe_data['Fertilizer Consumption (kg/ha)'],
            marker_color=bar_colors,
            text=[f"{v:.0f}" for v in fe_data['Fertilizer Consumption (kg/ha)']],
            textposition='outside',
            textfont=dict(color='#a0aec0', size=10),
            hovertemplate="<b>%{x}</b><br>%{y:.1f} kg/ha<extra></extra>",
        ))
        layout3 = chart_layout(y_title="kg/ha arable land", height=350)
        layout3['hovermode'] = 'x'
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("Data gaps represent years not yet published by World Bank.")
    else:
        st.info("Fertilizer data not available.")

    # ── Insight Box ─────────────────────────────────────────────
    if 'Food Production Index' in ke_all.columns and 'Cereal Yield (kg/ha)' in ke_all.columns:
        fpi_2000 = ke_all[ke_all['year'] == 2000]['Food Production Index'].values
        fpi_latest_v = ke_all.dropna(subset=['Food Production Index']).sort_values('year').iloc[-1]
        cy_latest_v = ke_all.dropna(subset=['Cereal Yield (kg/ha)']).sort_values('year').iloc[-1]

        fpi_base = float(fpi_2000[0]) if len(fpi_2000) > 0 and fpi_2000[0] else None
        fpi_now = float(fpi_latest_v['Food Production Index'])
        fpi_now_yr = int(fpi_latest_v['year'])
        cy_now = float(cy_latest_v['Cereal Yield (kg/ha)'])
        cy_now_yr = int(cy_latest_v['year'])

        pct_change = ((fpi_now - fpi_base) / fpi_base * 100) if fpi_base else None
        pct_str = f"up <strong>{pct_change:.0f}%</strong> from 2000" if pct_change else "trend data available"
        insight(
            f"Kenya's Food Production Index stands at <strong>{fpi_now:.1f}</strong> in {fpi_now_yr} "
            f"(2014–2016 = 100), {pct_str}. "
            f"Cereal yield reached <strong>{cy_now:,.0f} kg/ha</strong> in {cy_now_yr}. "
            "Despite drought shocks in 2009 and 2011, Kenya's agricultural output has maintained a "
            "long-run upward trend — driven by expanded arable land use and modest intensification.",
        )


# ══════════════════════════════════════════════════════════════
# TAB 2 — Food Security
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Food Security — Hunger, Imports & Economic Links")

    col_c, col_d = st.columns(2)

    # ── Chart 4: Undernourishment rate Kenya (area) ─────────────
    with col_c:
        if 'Undernourishment Rate (%)' in ke_f.columns:
            un_data = ke_f.dropna(subset=['Undernourishment Rate (%)']).copy()
            _un_latest_pct = float(un_data.sort_values('year').iloc[-1]['Undernourishment Rate (%)']) if not un_data.empty else 0
            st.markdown(f"#### Undernourishment Rate — {_un_latest_pct:.1f}% of Kenyans at Risk")
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(
                x=un_data['year'],
                y=un_data['Undernourishment Rate (%)'],
                name='Undernourishment %',
                line=dict(color='#ce1126', width=2.5),
                fill='tozeroy',
                fillcolor='rgba(206,17,38,0.2)',
                mode='lines+markers',
                marker=dict(size=5, color='#ce1126'),
                hovertemplate="<b>%{x}</b><br>%{y:.1f}% undernourished<extra></extra>",
            ))
            # Trend line
            if len(un_data) > 3:
                z = np.polyfit(un_data['year'], un_data['Undernourishment Rate (%)'], 1)
                p = np.poly1d(z)
                fig4.add_trace(go.Scatter(
                    x=un_data['year'],
                    y=p(un_data['year']),
                    name='Trend',
                    line=dict(color='#f5a623', width=1.5, dash='longdash'),
                    hoverinfo='skip',
                ))
            # Regional reference line at 20% (Sub-Saharan Africa benchmark target)
            if not un_data.empty:
                fig4.add_hline(
                    y=20,
                    line=dict(color='rgba(245,166,35,0.55)', width=1.5, dash='dot'),
                    annotation_text="20% regional target",
                    annotation_position="bottom right",
                    annotation_font=dict(color='#f5a623', size=10),
                )
                # Annotation at latest data point
                _un_latest_row = un_data.sort_values('year').iloc[-1]
                fig4.add_annotation(
                    x=int(_un_latest_row['year']),
                    y=float(_un_latest_row['Undernourishment Rate (%)']),
                    text=f"<b>{float(_un_latest_row['Undernourishment Rate (%)']):.1f}%</b>",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor='#ce1126',
                    arrowwidth=1.5,
                    ax=30,
                    ay=-30,
                    font=dict(color='#e2e8f0', size=12, family='Inter'),
                    bgcolor='rgba(206,17,38,0.25)',
                    bordercolor='rgba(206,17,38,0.5)',
                    borderwidth=1,
                    borderpad=4,
                )
            layout4 = chart_layout(y_title="% of population", height=380)
            fig4.update_layout(**layout4)
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.markdown("#### Undernourishment Rate — Kenya (%)")
            st.info("Undernourishment data not available.")

    # ── Chart 5: Multi-country undernourishment ─────────────────
    with col_d:
        st.markdown("#### Undernourishment — Regional Comparison")
        if 'Undernourishment Rate (%)' in comp_f.columns:
            fig5 = go.Figure()
            for eco in selected_codes:
                sub = comp_f[comp_f['economy'] == eco].dropna(subset=['Undernourishment Rate (%)'])
                if sub.empty:
                    continue
                is_ke = eco == 'KE'
                fig5.add_trace(go.Scatter(
                    x=sub['year'],
                    y=sub['Undernourishment Rate (%)'],
                    name=COUNTRY_NAMES.get(eco, eco),
                    line=dict(
                        color=COUNTRY_COLORS.get(eco, '#a0aec0'),
                        width=3 if is_ke else 1.8,
                    ),
                    mode='lines',
                    opacity=1.0 if is_ke else 0.75,
                    hovertemplate=f"<b>{COUNTRY_NAMES.get(eco, eco)}</b>: %{{y:.1f}}%<extra></extra>",
                ))
            layout5 = chart_layout(y_title="% of population", height=380)
            fig5.update_layout(**layout5)
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No data.")

    # ── Chart 6: Scatter — Ag% GDP vs Undernourishment ─────────
    st.markdown("#### Does Agricultural GDP Reduce Hunger? — Latest Year Comparison")
    if 'Agriculture % GDP' in dff.columns and 'Undernourishment Rate (%)' in dff.columns:
        scatter_data = []
        for eco in selected_codes:
            eco_df = df[df['economy'] == eco].dropna(
                subset=['Agriculture % GDP', 'Undernourishment Rate (%)']
            ).sort_values('year')
            if eco_df.empty:
                continue
            row = eco_df.iloc[-1]
            scatter_data.append({
                'country': COUNTRY_NAMES.get(eco, eco),
                'economy': eco,
                'agri_gdp': row['Agriculture % GDP'],
                'undernourishment': row['Undernourishment Rate (%)'],
                'year': int(row['year']),
            })

        if scatter_data:
            sdf = pd.DataFrame(scatter_data)
            fig6 = go.Figure()

            # Trend line
            if len(sdf) > 2:
                z = np.polyfit(sdf['agri_gdp'], sdf['undernourishment'], 1)
                p = np.poly1d(z)
                x_range = np.linspace(sdf['agri_gdp'].min() - 1, sdf['agri_gdp'].max() + 1, 50)
                fig6.add_trace(go.Scatter(
                    x=x_range, y=p(x_range),
                    name='Trend',
                    line=dict(color='rgba(245,166,35,0.4)', width=2, dash='dash'),
                    hoverinfo='skip',
                ))

            for _, row in sdf.iterrows():
                is_ke = row['economy'] == 'KE'
                fig6.add_trace(go.Scatter(
                    x=[row['agri_gdp']],
                    y=[row['undernourishment']],
                    mode='markers+text',
                    name=row['country'],
                    marker=dict(
                        size=20 if is_ke else 14,
                        color=COUNTRY_COLORS.get(row['economy'], '#a0aec0'),
                        line=dict(color='#fff', width=2 if is_ke else 0),
                        symbol='diamond' if is_ke else 'circle',
                    ),
                    text=[row['country']],
                    textposition='top center',
                    textfont=dict(size=11, color='#e2e8f0'),
                    hovertemplate=(
                        f"<b>{row['country']}</b> ({row['year']})<br>"
                        f"Ag % GDP: {row['agri_gdp']:.1f}%<br>"
                        f"Undernourishment: {row['undernourishment']:.1f}%<extra></extra>"
                    ),
                    showlegend=False,
                ))

            layout6 = chart_layout(
                x_title="Agriculture % of GDP",
                y_title="Undernourishment Rate (%)",
                height=380,
            )
            layout6['hovermode'] = 'closest'
            fig6.update_layout(**layout6)
            st.plotly_chart(fig6, use_container_width=True)

    # ── Insight Box ─────────────────────────────────────────────
    if 'Undernourishment Rate (%)' in ke_all.columns:
        un_latest = ke_all.dropna(subset=['Undernourishment Rate (%)']).sort_values('year').iloc[-1]
        un_v = float(un_latest['Undernourishment Rate (%)'])
        un_y = int(un_latest['year'])
        # EAC average from available data
        eac_codes = [c for c in ['UG', 'TZ', 'ET'] if c in selected_codes]
        eac_vals = []
        for eco in eac_codes:
            sub = df[(df['economy'] == eco)].dropna(subset=['Undernourishment Rate (%)'])
            if not sub.empty:
                eac_vals.append(float(sub.sort_values('year').iloc[-1]['Undernourishment Rate (%)']))
        eac_avg = np.mean(eac_vals) if eac_vals else None

        eac_str = (
            f"Compared to a regional peer average of <strong>{eac_avg:.1f}%</strong>, "
            f"Kenya performs {'better' if un_v < eac_avg else 'similarly or worse'}."
        ) if eac_avg else ""

        insight(
            f"In {un_y}, <strong>{un_v:.1f}%</strong> of Kenya's population faces undernourishment. "
            f"{eac_str} "
            "The long-run trend shows meaningful improvement since 2000, but progress has "
            "slowed in recent years amid climate shocks and rising food import costs.",
        )


# ══════════════════════════════════════════════════════════════
# TAB 3 — Structural Transformation
# ══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Structural Transformation — The Productivity Gap")

    # ── Chart 7: Structural Gap — Ag% GDP vs Ag Employment% ──────
    st.markdown("#### Agricultural Transformation Gap — Kenya")
    if 'Agriculture % GDP' in ke_f.columns and 'Agricultural Employment %' in ke_f.columns:
        ag_data = ke_f.dropna(subset=['Agriculture % GDP', 'Agricultural Employment %']).sort_values('year')
        fig7 = go.Figure()

        # GDP trace first (lower values) — fill upward to Employment trace
        fig7.add_trace(go.Scatter(
            x=ag_data['year'],
            y=ag_data['Agriculture % GDP'],
            name='Agriculture % of GDP',
            line=dict(color='#00d26a', width=2.5),
            mode='lines+markers',
            marker=dict(size=5),
            hovertemplate="Ag GDP share: <b>%{y:.1f}%</b><extra></extra>",
        ))

        # Employment trace — fill='tonexty' shades gap between this and GDP trace
        fig7.add_trace(go.Scatter(
            x=ag_data['year'],
            y=ag_data['Agricultural Employment %'],
            name='Employment in Agriculture (%)',
            line=dict(color='#f5a623', width=2.5),
            fill='tonexty',
            fillcolor='rgba(206,17,38,0.1)',
            mode='lines+markers',
            marker=dict(size=5),
            hovertemplate="Employment: <b>%{y:.1f}%</b><extra></extra>",
        ))

        # Productivity Gap annotation at latest year
        if not ag_data.empty:
            _latest_yr = int(ag_data['year'].iloc[-1])
            _emp_val = float(ag_data['Agricultural Employment %'].iloc[-1])
            _gdp_val = float(ag_data['Agriculture % GDP'].iloc[-1])
            _gap_val = _emp_val - _gdp_val
            _mid_y = (_emp_val + _gdp_val) / 2
            fig7.add_annotation(
                x=_latest_yr,
                y=_mid_y,
                text=f"<b>{_gap_val:.0f}pp gap</b>",
                showarrow=True,
                arrowhead=2,
                arrowcolor='#ce1126',
                arrowwidth=1.5,
                ax=-60,
                ay=0,
                font=dict(color='#ce1126', size=12, family='Inter'),
                bgcolor='rgba(15,23,41,0.85)',
                bordercolor='rgba(206,17,38,0.4)',
                borderwidth=1,
                borderpad=4,
            )
            # "Productivity Gap" label in the shaded area mid-chart
            _mid_yr = ag_data['year'].median()
            _mid_emp = float(ag_data[ag_data['year'] == ag_data['year'].median()]['Agricultural Employment %'].values[0]) if ag_data['year'].median() in ag_data['year'].values else _emp_val
            _mid_gdp = float(ag_data[ag_data['year'] == ag_data['year'].median()]['Agriculture % GDP'].values[0]) if ag_data['year'].median() in ag_data['year'].values else _gdp_val
            fig7.add_annotation(
                x=_mid_yr,
                y=(_mid_emp + _mid_gdp) / 2,
                text="Productivity Gap",
                showarrow=False,
                font=dict(color='rgba(206,17,38,0.7)', size=11, family='Inter'),
                bgcolor='rgba(0,0,0,0)',
            )

        layout7 = chart_layout(
            title="Agricultural Transformation Gap — Kenya",
            y_title="% (Employment / GDP share)",
            height=440,
        )
        layout7['legend']['orientation'] = 'h'
        layout7['legend']['y'] = 1.08
        fig7.update_layout(**layout7)
        st.plotly_chart(fig7, use_container_width=True)

    col_e, col_f = st.columns(2)

    # ── Chart 8: Horizontal bar — Employment % by country ──────
    with col_e:
        st.markdown("#### Agricultural Employment — Country Comparison (Latest Year)")
        if 'Agricultural Employment %' in dff.columns:
            emp_rows = []
            for eco in selected_codes:
                sub = df[df['economy'] == eco].dropna(subset=['Agricultural Employment %'])
                if sub.empty:
                    continue
                latest_row = sub.sort_values('year').iloc[-1]
                emp_rows.append({
                    'country': COUNTRY_NAMES.get(eco, eco),
                    'economy': eco,
                    'value': float(latest_row['Agricultural Employment %']),
                    'year': int(latest_row['year']),
                })
            if emp_rows:
                emp_df = pd.DataFrame(emp_rows).sort_values('value', ascending=True)
                bar_colors = [
                    '#00d26a' if r['economy'] == 'KE' else '#2d4a7a'
                    for _, r in emp_df.iterrows()
                ]
                fig8 = go.Figure(go.Bar(
                    x=emp_df['value'],
                    y=emp_df['country'],
                    orientation='h',
                    marker_color=bar_colors,
                    text=[f"{v:.1f}%" for v in emp_df['value']],
                    textposition='outside',
                    textfont=dict(color='#a0aec0', size=11),
                    hovertemplate="<b>%{y}</b>: %{x:.1f}%<extra></extra>",
                ))
                layout8 = chart_layout(x_title="% of total employment", height=360)
                layout8['hovermode'] = 'closest'
                layout8['xaxis']['range'] = [0, emp_df['value'].max() * 1.2]
                fig8.update_layout(**layout8)
                st.plotly_chart(fig8, use_container_width=True)

    # ── Chart 9: Food Imports vs Exports ────────────────────────
    with col_f:
        st.markdown("#### Food Trade Balance — Kenya (% of Merchandise Trade)")
        if 'Food Imports % Merch Imports' in ke_f.columns and 'Food Exports % Merch Exports' in ke_f.columns:
            trade_data = ke_f.dropna(
                subset=['Food Imports % Merch Imports', 'Food Exports % Merch Exports'],
                how='all',
            )
            fig9 = go.Figure()
            fig9.add_trace(go.Scatter(
                x=trade_data['year'],
                y=trade_data['Food Imports % Merch Imports'],
                name='Food Imports',
                line=dict(color='#ce1126', width=2.5),
                fill='tozeroy',
                fillcolor='rgba(206,17,38,0.1)',
                mode='lines',
                hovertemplate="Imports: <b>%{y:.1f}%</b><extra></extra>",
            ))
            fig9.add_trace(go.Scatter(
                x=trade_data['year'],
                y=trade_data['Food Exports % Merch Exports'],
                name='Food Exports',
                line=dict(color='#00d26a', width=2.5),
                fill='tozeroy',
                fillcolor='rgba(0,210,106,0.1)',
                mode='lines',
                hovertemplate="Exports: <b>%{y:.1f}%</b><extra></extra>",
            ))
            layout9 = chart_layout(y_title="% of merchandise trade", height=360)
            layout9['legend']['orientation'] = 'h'
            fig9.update_layout(**layout9)
            st.plotly_chart(fig9, use_container_width=True)
        else:
            st.info("Trade data not available.")

    # ── Insight Box ─────────────────────────────────────────────
    agdp_ok = 'Agriculture % GDP' in ke_all.columns
    empl_ok = 'Agricultural Employment %' in ke_all.columns
    if agdp_ok and empl_ok:
        agdp_row = ke_all.dropna(subset=['Agriculture % GDP']).sort_values('year').iloc[-1]
        empl_row = ke_all.dropna(subset=['Agricultural Employment %']).sort_values('year').iloc[-1]
        agdp_v = float(agdp_row['Agriculture % GDP'])
        agdp_y = int(agdp_row['year'])
        empl_v = float(empl_row['Agricultural Employment %'])
        empl_y = int(empl_row['year'])
        gap = empl_v - agdp_v
        insight(
            f"Agriculture employs <strong>{empl_v:.1f}%</strong> of Kenya's workforce ({empl_y}) "
            f"but contributes only <strong>{agdp_v:.1f}%</strong> of GDP ({agdp_y}) — "
            f"a <strong>{gap:.1f} percentage-point productivity gap</strong>. "
            "This structural divide means Kenya's agricultural workers generate far less output "
            "per head than the broader economy — the defining challenge of Kenya's rural development.",
            variant="warning",
        )


# ══════════════════════════════════════════════════════════════
# TAB 4 — Export Data
# ══════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Explore & Download Raw Data")

    col_g, col_h = st.columns([2, 1])
    with col_g:
        country_filter = st.selectbox(
            "Filter by Country",
            ['All'] + [COUNTRY_NAMES[c] for c in COUNTRY_NAMES],
        )
    with col_h:
        yr_filter = st.slider("Year Range", 2000, 2024, (2000, 2024), key="export_yr")

    export_df = df[df['year'].between(yr_filter[0], yr_filter[1])].copy()
    if country_filter != 'All':
        eco_code = COUNTRY_NAMES_INV[country_filter]
        export_df = export_df[export_df['economy'] == eco_code]

    # Reorder columns for readability
    priority_cols = ['country', 'economy', 'year']
    remaining = [c for c in export_df.columns if c not in priority_cols]
    export_df = export_df[priority_cols + remaining].sort_values(['economy', 'year'])

    st.markdown(f"**{len(export_df):,} rows** · {export_df['year'].min()}–{export_df['year'].max()}")
    st.dataframe(
        export_df.style.format(
            {c: "{:.2f}" for c in export_df.select_dtypes('float').columns},
            na_rep="—",
        ),
        use_container_width=True,
        height=400,
    )

    # Excel download
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, sheet_name='Kenya Agri Data', index=False)
    st.download_button(
        label="⬇️  Download as Excel",
        data=buffer.getvalue(),
        file_name=f"kenya_agri_pulse_{yr_filter[0]}_{yr_filter[1]}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Parquet download
    pq_buffer = io.BytesIO()
    export_df.to_parquet(pq_buffer, index=False)
    st.download_button(
        label="⬇️  Download as Parquet",
        data=pq_buffer.getvalue(),
        file_name=f"kenya_agri_pulse_{yr_filter[0]}_{yr_filter[1]}.parquet",
        mime="application/octet-stream",
    )

    st.markdown("---")
    st.markdown("**Data Dictionary**")
    meta_rows = [
        {"Indicator": label, "World Bank Code": code, "Unit": "See WDI documentation"}
        for code, label in {
            'AG.PRD.FOOD.XD': 'Food Production Index',
            'AG.PRD.LVSK.XD': 'Livestock Production Index',
            'AG.YLD.CREL.KG': 'Cereal Yield (kg/ha)',
            'AG.LND.ARBL.ZS': 'Arable Land (% land)',
            'AG.LND.AGRI.ZS': 'Agricultural Land (% land)',
            'NV.AGR.TOTL.ZS': 'Agriculture % GDP',
            'SL.AGR.EMPL.ZS': 'Agricultural Employment %',
            'SN.ITK.DEFC.ZS': 'Undernourishment Rate (%)',
            'TM.VAL.FOOD.ZS.UN': 'Food Imports % Merch Imports',
            'TX.VAL.FOOD.ZS.UN': 'Food Exports % Merch Exports',
            'AG.CON.FERT.ZS': 'Fertilizer Consumption (kg/ha)',
            'SP.RUR.TOTL.ZS': 'Rural Population %',
            'NE.IMP.GNFS.CD': 'Imports Goods Services (USD)',
            'SP.POP.TOTL': 'Population',
        }.items()
    ]
    st.dataframe(pd.DataFrame(meta_rows), use_container_width=True, hide_index=True)
