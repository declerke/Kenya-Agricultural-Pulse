# ðŸŒ¾ Kenya Agricultural Pulse: Food Security, Crop Yields & Agricultural Transformation Dashboard

**Kenya Agricultural Pulse** is a production-grade Streamlit BI dashboard that fetches 14 World Bank World Development Indicator series for Kenya and four peer economies â€” Uganda, Tanzania, Ethiopia, and Nigeria â€” across 25 years (2000â€“2024) via direct HTTP calls to the World Bank REST API v2, persists 125 rows of clean, merged data to a Parquet file using PyArrow, and renders 9 interactive Plotly charts across 4 analytical tabs that tell the complete story of Kenya's food basket: how production indices and cereal yields have trended through five drought cycles and COVID supply disruptions; how 36.8% of Kenyans face undernourishment despite a rising Food Production Index; how agriculture employs 46.5% of Kenya's workforce yet contributes only 22.5% of GDP â€” a 24-percentage-point structural productivity gap that is the defining economic challenge of Kenya's rural sector; and how Kenya's food trade balance, fertilizer intensification trends, and agricultural employment compare against its East African peers and Nigeria as a continental anchor. The pipeline handles a documented API edge case â€” the World Bank's Food and Livestock Production Indices return 400 Bad Request errors on multi-country batch calls and must be fetched one country at a time â€” and all computation, data storage, and visualisation runs entirely on free, open-source tooling at zero marginal cost.

| Metric | Value |
|--------|-------|
| Total rows in Parquet | 125 (5 countries Ã— 25 years, 2000â€“2024) |
| Indicators fetched | 14 of 15 attempted (Cereal Production MT excluded â€” persistent API timeout) |
| Comparison countries | Kenya, Uganda, Tanzania, Ethiopia, Nigeria |
| Dashboard tabs | 4 (Production & Yields Â· Food Security Â· Structural Transformation Â· Export Data) |
| Interactive charts | 9 Plotly charts (go + express) |
| KPI cards | 4 (Food Production Index Â· Cereal Yield Â· Undernourishment Rate Â· Agriculture % GDP) |
| Lines of code | 990 |
| Agricultural employment (Kenya 2024) | 46.5% of total workforce |
| Agriculture % GDP (Kenya 2024) | 22.5% |
| Structural productivity gap | 24 percentage points |
| Undernourishment rate (Kenya 2023) | 36.8% â€” nearly 1 in 3 Kenyans |
| Food Production Index (Kenya 2022) | 112.4 (baseline 2014â€“2016 = 100) |
| Cereal yield (Kenya 2023) | 1,758 kg/ha |
| Cost to run | $0 â€” open data + local stack only |

---

## ðŸŽ¯ Project Goal

Kenya's agricultural sector sits at the intersection of food security, rural employment, and macroeconomic transformation â€” yet the data needed to understand that intersection is scattered across dozens of World Bank indicator series, rarely assembled into a single analytical view, and almost never accompanied by the contextual annotations (drought years, COVID disruption, regional benchmarks) that turn time-series numbers into a policy narrative. Publicly available dashboards covering Kenya's agricultural transformation from the perspective of both productivity and food security are essentially non-existent in the open-source space.

Kenya Agricultural Pulse builds that dashboard on real data. The World Bank WDI API provides 14 production, land use, food security, employment, and trade indicators for Kenya and four peer economies across a 25-year window. The pipeline assembles those indicators into a single analytical frame and renders them as an integrated BI dashboard aimed at agricultural economists, development practitioners, and data engineers who want to understand â€” or demonstrate the ability to analyse â€” Sub-Saharan agricultural transformation. Every design choice in the dashboard prioritises analytical insight over data display: the structural gap chart uses shaded fill between two series to make a 24pp disparity immediately legible; the undernourishment chart carries a regional target reference line and a dynamic title that reports the current year's rate; event annotations on the Food Production Index chart convert apparent noise into a readable pattern of drought-driven shocks. The result is a dashboard that argues a specific thesis â€” Kenya's agricultural sector is structurally under-productive relative to its employment share, and food insecurity remains elevated despite improving production trends â€” rather than merely displaying numbers.

---

## ðŸ§¬ System Architecture

1. **Data Ingestion â€” World Bank REST API v2:** `data_pipeline.py` constructs requests against `https://api.worldbank.org/v2/country/{country}/indicator/{code}?format=json&per_page=500&date=2000:2024` for each of the 14 indicators. Standard indicators use semicolon-separated country codes in a single multi-country URL, retrieving all 5 countries' data in one request per indicator. The pipeline handles multi-page responses by inspecting `payload[0]['pages']` and issuing additional `&page=N` requests until all records are retrieved. For two production index indicators that return 400 errors on multi-country calls (`AG.PRD.FOOD.XD` and `AG.PRD.LVSK.XD`), the pipeline loops over each country code individually with a 200ms inter-request sleep, adding approximately 10 seconds to pipeline runtime in exchange for complete data retrieval. Each indicator request is wrapped in a try/except that prints a skip message and returns `None` rather than failing the entire pipeline, so a single API timeout does not abort the run.

2. **Data Normalisation and Parquet Persistence:** Raw API records map ISO3 country codes to the 5-character ISO2 codes used internally via a `COUNTRY_ISO3` lookup dict. Each indicator's records are assembled into a per-indicator DataFrame with columns `[economy, year, <indicator_label>]`. All 14 indicator DataFrames are left-joined onto a complete `(economy Ã— year)` base grid of 125 rows â€” one for every combination of 5 countries and 25 years â€” ensuring that coverage gaps appear as `NaN` values rather than missing rows. A `country` display-name column is added from `COUNTRY_NAMES` mapping. The merged 125-row DataFrame is written to `data/processed/agri.parquet` using PyArrow; the columnar format enables fast column-subset reads that pair well with Streamlit's `@st.cache_data` pattern. The pipeline prints a Kenya-specific coverage report showing each indicator's non-null count out of 25 with an ASCII progress bar.

3. **Streamlit Dashboard and State Management:** `app.py` loads the Parquet file once at startup via `@st.cache_data` and derives filtered views (`ke_f` for Kenya in the selected year range, `comp_f` for all selected countries, `ke_all` unfiltered for KPI calculations). A sidebar year-range slider (2000â€“2024) and a multi-select for peer countries (Uganda, Tanzania, Ethiopia, Nigeria â€” defaulting to Uganda, Tanzania, Ethiopia) drive all chart filters without reloading data. Four KPI metric cards at the top of the page compute latest-value and 10-year delta for Food Production Index, Cereal Yield, Undernourishment Rate, and Agriculture % GDP using a `latest_val()` helper that handles sparse series by finding the most recent non-null row. A `latest_val()` call on Agriculture % GDP with `delta_color="inverse"` correctly signals that a rising share is neutral-to-positive context.

4. **CSS Injection and Dark BI Theme:** The dashboard's visual design is implemented entirely via `st.markdown(CUSTOM_CSS, unsafe_allow_html=True)` rather than Streamlit's native theming system, which cannot override per-component gradients or tab active-state colours. The injected CSS sets the app background to `#060b17`, imports Inter font from Google Fonts, applies a `linear-gradient(135deg, #0f1729, #1a2744)` to all `[data-testid="metric-container"]` elements with a `#00d26a` left border accent, styles tab active states with a `#00d26a` background and black text, and renders callout insight boxes in two variants â€” amber-bordered warning boxes and green-bordered positive-signal boxes. Plotly chart backgrounds use `rgba(0,0,0,0)` for `paper_bgcolor` and `rgba(11,18,40,0.6)` for `plot_bgcolor` to integrate with the app background without a box outline.

5. **Plotly Chart Layer:** Nine charts are distributed across three analysis tabs. Tab 1 (Production & Yields) contains a Kenya-only dual-series Food + Livestock Production Index time series with four event annotations via `add_vline`, a 5-country Cereal Yield comparison line chart with Kenya's line bolded and area-filled in green, and a Kenya fertilizer consumption bar chart with a `lerp_color()` function that interpolates redâ†’amberâ†’green across normalised bar values. Tab 2 (Food Security) contains a Kenya undernourishment area chart with a trend-line overlay, a 20% regional target reference line, and a callout annotation at the latest data point; a 5-country undernourishment comparison line chart; and an Agriculture % GDP vs Undernourishment scatter plot with a trend line. Tab 3 (Structural Transformation) contains the structural gap area chart, a horizontal bar chart comparing latest-year agricultural employment across all selected countries, and a food imports vs exports dual-area trade balance chart. Tab 4 (Export Data) contains an interactive filterable data table with Excel and Parquet download buttons.

---

## ðŸ› ï¸ Technical Stack

| Layer | Tool | Version |
|---|---|---|
| Data ingestion | World Bank REST API v2 (requests) | requests 2.34+ |
| Data storage | Parquet (PyArrow) | pyarrow 16.0+ |
| Data processing | pandas, numpy | pandas 2.2+, numpy 2.0+ |
| Dashboard | Streamlit | 1.45+ |
| Visualisation | Plotly Graph Objects + Express | 5.24+ |
| Excel export | openpyxl | 3.1.5+ |
| Environment | Python 3.11, uv | â€” |
| Cost | $0 | open data only |

---

## ðŸ“Š Performance & Results

- **Pipeline runtime:** full 14-indicator fetch completes in approximately 55â€“70 seconds depending on World Bank API response times; the two single-country loop indicators (`AG.PRD.FOOD.XD`, `AG.PRD.LVSK.XD`) add ~10 seconds relative to a pure batch call approach, which is acceptable for a pipeline that runs once to populate the local Parquet cache.
- **Kenya data coverage:** Agriculture % GDP and Agricultural Employment % are fully populated at 25/25 years; Food Production Index and Livestock Production Index have 23/25 years (2 years not yet published by World Bank); Cereal Yield and Arable/Agricultural Land are 24/25 years; Undernourishment Rate is 23/25 years; Food/Livestock Imports and Exports are 22/25 years.
- **Parquet file size:** 125 rows Ã— 17 columns (2 identity columns + 14 indicator columns + 1 display name) serialises to under 50 KB, enabling sub-millisecond cache-hit reads in Streamlit.
- **Dashboard load time:** first load triggers `@st.cache_data` Parquet read in under 50ms; all 9 charts are computed in-memory on the filtered DataFrame with no secondary I/O; chart re-renders on slider or multiselect change complete in under 200ms.
- **Key analytical findings surfaced:**
  - Kenya's agricultural productivity gap stands at **24 percentage points** (46.5% employment share vs 22.5% GDP share as of 2024) â€” the largest structural disparity among the 5 countries studied.
  - Undernourishment has declined from above 40% in the early 2000s to 36.8% in 2023 but remains well above the 20% Sub-Saharan target reference line.
  - Cereal yield (1,758 kg/ha in 2023) is broadly in line with Uganda and Tanzania but substantially below Nigeria's trajectory, suggesting limited intensification gains relative to continental peers.
  - The Food Production Index (112.4 in 2022, baseline 2014â€“2016 = 100) shows a long-run upward trend with clearly identifiable dips at the annotated drought years: 2009, 2011, and 2017.
  - Kenya runs a persistent food trade imbalance â€” food imports as a share of merchandise imports consistently exceed food exports as a share of merchandise exports, indicating structural food import dependence.

---

## ðŸŒ Live Dashboard

Run locally after fetching data:

```powershell
# Clone and set up environment
git clone https://github.com/declerke/Kenya-Agricultural-Pulse
cd Kenya-Agricultural-Pulse
uv venv .venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt

# Step 1 â€” fetch World Bank data (~60 seconds)
python data_pipeline.py

# Step 2 â€” launch dashboard
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`. Use the sidebar year-range slider to narrow the analysis window and the peer country multi-select to add or remove comparison economies. All 9 charts update dynamically without a data reload.

**Sidebar controls:**
- Year range slider: 2000â€“2024 (affects all chart filters except KPI cards, which always use the full 25-year window for delta calculations)
- Peer country multi-select: Uganda, Tanzania, Ethiopia, Nigeria (Kenya is always included; defaults to Uganda, Tanzania, Ethiopia)

---

## ðŸ“‘ Data Sources

All data is sourced from the **World Bank World Development Indicators (WDI)** database, accessed via the public REST API v2 at `https://api.worldbank.org/v2/`. No API key is required. Data is fetched live when `data_pipeline.py` is run and cached to `data/processed/agri.parquet` for all subsequent dashboard launches.

**Coverage period:** 2000â€“2024 (25 years)  
**Reporting entities:** Kenya (KE), Uganda (UG), Tanzania (TZ), Ethiopia (ET), Nigeria (NG)  
**WDI source ID:** [World Development Indicators](https://databank.worldbank.org/source/world-development-indicators)

---

## ðŸ§  Key Design Decisions

**Cereal Production (MT) excluded in favour of Cereal Yield (kg/ha):** The World Bank indicator `AG.PRD.CREL.MT` (cereal production in metric tons) consistently timed out across all tested call patterns during pipeline development â€” single-country requests, multi-country batch calls, and timeout thresholds up to 120 seconds all produced connection errors rather than data. Rather than include an indicator that would cause intermittent pipeline failures or require fragile retry loops, the project substitutes Cereal Yield (`AG.YLD.CREL.KG`, kg per hectare of arable land), which is not only more reliable via the API but is analytically superior for the agricultural transformation narrative. Yield per hectare measures productivity and intensification â€” the improvement in output per unit of land â€” which is a more relevant policy signal than raw tonnage, which scales mechanically with population and arable land area rather than with productivity gains. An agricultural economy expanding its cereal production by bringing new land under cultivation is doing something fundamentally different from one expanding production by intensifying inputs on existing land, and yield isolates the latter. This substitution removes one indicator (15 attempted â†’ 14 fetched) while improving the analytical precision of the production layer.

**`fill='tonexty'` shading between Employment and GDP lines for the structural gap:** The "agricultural transformation gap" â€” the difference between agriculture's share of employment and its share of GDP â€” is the central analytical insight of the Structural Transformation tab, and the magnitude of that gap at each year is the single most important number in the entire dashboard. Rendering both series as plain lines without fill forces the viewer to visually estimate the gap at each year, which is cognitively demanding and imprecise. Using Plotly's `fill='tonexty'` on the Employment trace renders the space between the two lines as a continuous shaded region, making the gap's magnitude and its trajectory across 25 years immediately legible at a glance. The fill colour â€” `rgba(206,17,38,0.1)` in Kenya's national red â€” carries deliberate connotative weight: the gap is a problem requiring policy attention, not a neutral distributional statistic. The dual-trace approach with GDP drawn first (lower values) and Employment second (higher values) ensures the shading fills correctly between the two, and annotations at the latest year and at the chart midpoint label both the current gap value and the region as "Productivity Gap" so the chart is self-explanatory without a written caption.

**Nigeria as the fifth comparison country instead of Rwanda:** Restricting the comparison set to East African Community members â€” Kenya, Uganda, Tanzania, and Ethiopia â€” would produce a peer group with limited analytical range, since all four operate in broadly similar agro-ecological zones, face comparable ENSO-driven drought exposure, and have agricultural employment shares clustered in the same 60â€“75% band. Adding Nigeria as the fifth country provides a West African anchor that dramatically expands the interpretive range of every peer comparison chart. As Africa's most populous country and largest economy (by GDP), Nigeria represents an agricultural economy at a different stage of structural transformation: higher industrial output share, more diversified export base, and a trajectory toward lower agricultural employment share over the same 25-year window. This makes Nigeria a meaningful reference point for what large-population agricultural economies look like at different points of the transformation path â€” which is exactly the question the Structural Transformation tab is designed to answer. Rwanda was the obvious alternative (compact, intensively studied, rapidly transforming) but would have added a fourth EAC member without the continental scope that Nigeria provides.

**Food and Livestock Production Indices fetched one country at a time:** The World Bank API returns a 400 Bad Request response when `AG.PRD.FOOD.XD` (Food Production Index) or `AG.PRD.LVSK.XD` (Livestock Production Index) are requested for multiple countries using a semicolon-separated country list in a single URL â€” the standard pattern that works correctly for all 12 other indicators in this pipeline. These indices appear to be stored in a different database partition from standard WDI indicators, and the multi-country batch endpoint does not support cross-partition queries for them. The pipeline handles this by maintaining a `SINGLE_COUNTRY_INDICATORS` set containing these two codes and branching in `fetch_indicator()`: if the code is in the set, it loops over each of the 5 country codes individually, adds the records to a shared list, and sleeps 200ms between calls to avoid rate-limiting. This adds approximately 10 seconds to pipeline runtime (5 requests Ã— ~2s API latency each Ã— 2 indicators) but guarantees complete data retrieval. Wrapping the branch in the existing per-indicator try/except means a timeout on a single country request causes only that country's data to be missing rather than aborting the indicator entirely. The approach was confirmed correct by inspecting the World Bank API documentation for `format=json` batch country calls, which notes the semicolon-separated pattern as the recommended approach without documenting the production index exception.

**2009, 2011, and 2017 drought annotations on the Food Production Index chart:** Kenya's food production is highly sensitive to rainfall variability â€” the country experiences recurring drought cycles driven by Indian Ocean Dipole and ENSO patterns that produce La NiÃ±a-linked short-rain failures. Without annotation, the resulting year-to-year dips in Kenya's Food Production Index time series are visually indistinguishable from random sampling noise or data quality artefacts. The 2009 drought, the 2011 East Africa drought (one of the most severe on record â€” declared a humanitarian famine in parts of Somalia, Ethiopia, and Kenya, affecting over 13 million people), and the 2017 drought are all clearly visible as production dips when the chart is annotated. Adding vertical reference lines at these years, labelled with event names rotated 90 degrees along the line, transforms the chart from a passive data display into an active analytical narrative about climate exposure and food security risk. The 2020 COVID Supply Disruptions annotation is added in amber rather than red to distinguish a supply-chain event from a direct production shock â€” both types of disruption appear in the same time series, and the colour distinction communicates that conceptual difference without requiring a text explanation. This annotation approach was implemented using Plotly's `add_vline()` with per-event colour and label rather than scatter trace annotations, which keeps the event markers properly aligned to year boundaries rather than floating between data points.

**Pre-existing NameError bug found and fixed during review:** The Export Data tab's country filter logic referenced the variable `COUNTRIES` (a list defined in `data_pipeline.py`) rather than the correct `COUNTRY_NAMES` dict (defined in `app.py`). This would have raised a `NameError: name 'COUNTRIES' is not defined` on any user interaction with the country filter dropdown. The fix was a one-line substitution: replacing `[COUNTRIES[c] for c in COUNTRY_NAMES]` with `[COUNTRY_NAMES[c] for c in COUNTRY_NAMES]` in the `st.selectbox` options list. The bug did not affect any other tab because only the Export tab builds a selectbox from `COUNTRY_NAMES` keys â€” the other tabs use `selected_codes` derived from the sidebar multiselect, which is correctly wired to `peer_options` values.

---

## ðŸ“‚ Project Structure

```
kenya-agri-pulse/
â”œâ”€â”€ app.py                          # Streamlit dashboard â€” 9 charts, 4 tabs, dark BI theme, 990 lines total
â”œâ”€â”€ data_pipeline.py                # World Bank REST API v2 fetch â†’ Parquet; handles single-country loop for production indices
â”œâ”€â”€ requirements.txt                # Pinned dependencies: streamlit, plotly, pandas, pyarrow, requests, openpyxl, numpy
â”œâ”€â”€ .gitignore                      # Excludes .venv/, data/processed/, __pycache__/, projectsummary.md
â”œâ”€â”€ assets/                         # Static assets folder (screenshots added post-run)
â””â”€â”€ data/
    â””â”€â”€ processed/
        â””â”€â”€ agri.parquet            # 125 rows Ã— 17 columns â€” generated by data_pipeline.py, gitignored
```

---

## âš™ï¸ Installation & Setup

**Prerequisites:** Python 3.11+, `uv` package manager, internet connection for World Bank API.

```powershell
# 1. Clone the repository
git clone https://github.com/declerke/Kenya-Agricultural-Pulse
cd Kenya-Agricultural-Pulse

# 2. Create virtual environment and install dependencies
uv venv .venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt

# 3. Fetch World Bank data (runs once, ~60 seconds)
#    Creates data/processed/agri.parquet (125 rows, ~50 KB)
python data_pipeline.py

# 4. Launch the Streamlit dashboard
streamlit run app.py
#    Opens at http://localhost:8501
```

**What `data_pipeline.py` prints on success:**

```
Fetching World Bank agricultural data (2000-2024)...
Indicators: 14, Countries: ['KE', 'UG', 'TZ', 'ET', 'NG']

  Fetched: Food Production Index                         115/125 non-null
  Fetched: Livestock Production Index                    115/125 non-null
  Fetched: Cereal Yield (kg/ha)                          120/125 non-null
  ...
  Fetched: Population                                    125/125 non-null

=== Kenya data coverage ===
  Agriculture % GDP                          25/25  [#########################]
  Agricultural Employment %                  25/25  [#########################]
  Food Production Index                      23/25  [#######################..]
  Undernourishment Rate (%)                  23/25  [#######################..]
  ...

Saved 125 rows total
Year range: 2000â€“2024
Countries: ['ET', 'KE', 'NG', 'TZ', 'UG']
Pipeline complete.
```

**No API key required.** The World Bank WDI REST API is publicly accessible without authentication.

---

## ðŸ“ˆ Indicator Reference

| World Bank Code | Indicator | Unit | Kenya Coverage |
|---|---|---|---|
| `AG.PRD.FOOD.XD` | Food Production Index | Index (2014â€“2016 = 100) | 23/25 yrs |
| `AG.PRD.LVSK.XD` | Livestock Production Index | Index (2014â€“2016 = 100) | 23/25 yrs |
| `AG.YLD.CREL.KG` | Cereal Yield | kg per hectare of arable land | 24/25 yrs |
| `AG.LND.ARBL.ZS` | Arable Land | % of land area | 24/25 yrs |
| `AG.LND.AGRI.ZS` | Agricultural Land | % of land area | 24/25 yrs |
| `NV.AGR.TOTL.ZS` | Agriculture, value added | % of GDP | 25/25 yrs |
| `SL.AGR.EMPL.ZS` | Employment in agriculture | % of total employment | 25/25 yrs |
| `SN.ITK.DEFC.ZS` | Prevalence of undernourishment | % of population | 23/25 yrs |
| `TM.VAL.FOOD.ZS.UN` | Food imports | % of merchandise imports | 22/25 yrs |
| `TX.VAL.FOOD.ZS.UN` | Food exports | % of merchandise exports | 22/25 yrs |
| `AG.CON.FERT.ZS` | Fertilizer consumption | kg per hectare of arable land | 24/25 yrs |
| `SP.RUR.TOTL.ZS` | Rural population | % of total population | 25/25 yrs |
| `NE.IMP.GNFS.CD` | Imports of goods and services | Current USD | 25/25 yrs |
| `SP.POP.TOTL` | Population, total | Count | 25/25 yrs |

**Excluded indicator:** `AG.PRD.CREL.MT` (Cereal Production in metric tons) â€” excluded due to persistent API timeout across all call patterns. Replaced analytically by Cereal Yield (`AG.YLD.CREL.KG`), which is a more meaningful productivity measure. See Key Design Decisions for full rationale.

---

## ðŸŽ“ Skills Demonstrated

| Skill | Evidence in This Project | Relevant Job Requirement |
|---|---|---|
| **REST API integration** | Direct `requests` calls to World Bank v2 API; multi-page pagination via `payload[0]['pages']`; per-indicator error handling; documented handling of the Food/Livestock Production Index 400-error edge case | "Integrate with third-party REST APIs and handle real-world API quirks" |
| **ETL pipeline design** | 14-indicator multi-country fetch, ISO3â†’ISO2 normalisation, full `(economy Ã— year)` left-join merge, coverage reporting, Parquet persistence â€” all in a single self-contained script | "Design and implement end-to-end data pipelines" |
| **Parquet and columnar storage** | PyArrow Parquet write; `@st.cache_data` read pattern; understanding of why columnar format benefits column-subset analytical reads | "Work with columnar storage formats (Parquet, ORC)" |
| **Streamlit dashboard architecture** | Multi-tab layout with sidebar controls; `@st.cache_data` caching; filtered view derivation; KPI cards with period-over-period delta; graceful handling of sparse series via `latest_val()` helper | "Build interactive BI dashboards for non-technical stakeholders" |
| **Plotly advanced visualisation** | `fill='tonexty'` structural gap chart; `lerp_color()` redâ†’amberâ†’green bar gradient; `add_vline()` event annotations; `add_hline()` reference lines; `add_annotation()` callout arrows; dual-series fills; scatter with trend line | "Create production-grade interactive charts with Plotly or similar" |
| **Data storytelling** | 24pp structural gap insight box; dynamic chart title reporting live undernourishment rate; executive summary banner with computed gap; drought annotations converting noise to narrative | "Translate raw data into actionable insights for business stakeholders" |
| **CSS injection and frontend theming** | Custom dark BI theme via `st.markdown(unsafe_allow_html=True)`; `linear-gradient` metric cards; Inter font; active tab override; insight box variants; Plotly `paper_bgcolor` / `plot_bgcolor` dark integration | "Implement custom UI/UX in data applications" |
| **Debugging real API behaviour** | Identified and documented World Bank 400 error for production index multi-country batch calls; implemented single-country loop workaround; fixed `COUNTRIES` â†’ `COUNTRY_NAMES` NameError in Export tab | "Diagnose and resolve API and runtime errors in production pipelines" |
| **Agricultural economics domain knowledge** | ENSO drought cycle context; IFRS 9-equivalent structural transformation narrative; undernourishment vs food production index decoupling analysis; agricultural value-added vs employment share as structural transformation metric | "Apply domain knowledge to contextualise analytical findings" |
| **Python best practices** | Module-level constants; type hints on helper functions; `try/except` per-indicator rather than pipeline-level; `os.makedirs(exist_ok=True)`; `io.BytesIO` for in-memory Excel/Parquet download buffers | "Write clean, maintainable Python for production data engineering" |

---

## ðŸ‘¤ Author

Ian Mwendwa Mboyo â€” Data Engineer  
[GitHub](https://github.com/declerke) Â· [Portfolio](https://ian-mwendwa.vercel.app)

