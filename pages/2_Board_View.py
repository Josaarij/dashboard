import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

from metrics_definitions import ALL_METRICS

st.set_page_config(layout="wide")
st.title("Hallituksen strateginen tilannekuva")

st.markdown(
    """
    <style>
      :root{
        --bg: #0b0b0b;
        --text: #f2f2f2;
        --muted: #b7b7b7;
        --gold: #caa64a;
        --gold2:#e1c36b;
        --border: rgba(202,166,74,0.22);
      }

      [data-testid="stSidebar"] { display: none; }
      [data-testid="stSidebarNav"] { display: none; }
      section.main > div { padding-left: 1rem !important; }

      .stApp{
        background: radial-gradient(1200px 800px at 15% 10%, #161616 0%, var(--bg) 55%, #070707 100%);
        color: var(--text);
      }

      h1 { font-size: 1.55rem !important; letter-spacing: .3px; }
      h2 { font-size: 1.20rem !important; margin-top: .25rem !important; }
      h3 { font-size: 1.05rem !important; }
      p, li, span, div { font-size: 0.95rem; }
      .block-container { padding-top: 1rem; padding-bottom: 1rem; }
      hr { border-color: rgba(255,255,255,0.08) !important; }

      .kpi-category{
        margin: 0.25rem 0 0.35rem 0;
        padding: .35rem .65rem;
        border-left: 4px solid var(--gold);
        background: linear-gradient(90deg, rgba(202,166,74,0.12), rgba(202,166,74,0.02));
        border-radius: 10px;
        font-weight: 750;
        letter-spacing: .4px;
      }

      .kpi-card{
        background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: .65rem .75rem .55rem .75rem;
        box-shadow: 0 10px 24px rgba(0,0,0,0.30);
        margin-bottom: .75rem;
        overflow: hidden;
      }

      .kpi-title{
        display:flex;
        align-items:flex-start;
        justify-content:space-between;
        gap:.6rem;
        margin-bottom:.20rem;
      }

      .kpi-name{
        font-weight: 780;
        letter-spacing:.2px;
        color: var(--text);
        font-size: 0.95rem;
        line-height: 1.15rem;
        flex: 1 1 auto;
        min-width: 0;
        white-space: normal;
        overflow-wrap: anywhere;
        word-break: break-word;
      }

      .kpi-status{
        font-size: 1.15rem;
        filter: drop-shadow(0 1px 1px rgba(0,0,0,0.35));
        flex: 0 0 auto;
        margin-top: 0.02rem;
      }

      .kpi-value{
        font-size: 1.25rem;
        font-weight: 900;
        color: var(--gold2);
        line-height: 1.35rem;
        margin: .10rem 0 .25rem 0;
      }

      .kpi-meta{
        color: var(--muted);
        font-size: 0.82rem;
        margin-bottom: .25rem;
      }

      .forecast-title{
        color: var(--gold2);
        font-size: 0.88rem;
        font-weight: 800;
        margin: .25rem 0 .35rem 0;
      }

      .risk-box{
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: .65rem .75rem;
      }

      .js-plotly-plot, .plot-container { background: transparent !important; }

      button[kind="secondary"]{
        padding: .15rem .45rem !important;
        min-height: 2rem !important;
        border-radius: 10px !important;
        border: 1px solid rgba(202,166,74,0.35) !important;
        background: rgba(202,166,74,0.10) !important;
        color: #f2f2f2 !important;
      }

      button[kind="secondary"] *{
        font-size: 1.05rem !important;
        font-weight: 900 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.popover("☰"):
    st.markdown("### Valikko")
    st.page_link("pages/2_Board_View.py", label="Board View", icon="📊")
    st.page_link("pages/1_Yllapito.py", label="Ylläpito", icon="🛠️")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)


def clean_number(v):
    return pd.to_numeric(
        str(v).replace("\u00a0", "").replace(" ", "").replace(",", "."),
        errors="coerce"
    )


def get_status(value: float, target: float, warning: float, direction: str) -> str:
    if direction == "up":
        if value >= target:
            return "🟢"
        if value >= warning:
            return "🟡"
        return "🔴"
    if value <= target:
        return "🟢"
    if value <= warning:
        return "🟡"
    return "🔴"


def fmt_value(metric_name: str, v) -> str:
    x = clean_number(v)
    if pd.isna(x):
        return "—"

    name = metric_name.lower()

    if "kassa" in name or "tulos" in name or "tuotot" in name:
        return f"{x:,.0f} €".replace(",", " ")
    if "%" in metric_name or "kattavuus" in name or "pysyvyys" in name or "koulutetut" in name:
        return f"{x:.0f} %"
    if "tyytyväisyys" in name:
        return f"{x:.1f} / 5"
    if "valmentajamäärä/joukkue" in name:
        return f"{x:.1f}"
    if abs(x) >= 1000:
        return f"{x:,.0f}".replace(",", " ")
    return f"{x:.1f}" if x % 1 != 0 else f"{x:.0f}"


def prepare_time_series(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date_clean"] = pd.to_datetime(out["date"], errors="coerce")
    out["value_clean"] = out["value"].apply(clean_number)
    out = out.dropna(subset=["date_clean", "value_clean"]).copy()
    out = out.sort_values("date_clean")
    out = out.drop_duplicates(subset=["date_clean"], keep="last")
    out["value"] = out["value_clean"]
    return out


resp = supabase.table("kpi_snapshots").select("*").execute()
data = pd.DataFrame(resp.data)

if data.empty:
    st.warning("Ei tallennettua dataa.")
    st.stop()

data["date"] = pd.to_datetime(data["date"], errors="coerce")
data = data.dropna(subset=["date"]).copy()

latest = (
    data.sort_values("date")
    .groupby("metric", as_index=False)
    .tail(1)
)

latest_by_metric = {}
for _, row in latest.iterrows():
    latest_by_metric[row["metric"]] = row

critical = []
warning_list = []

cash_detail_metrics = [
    "Kassa – viimeisin toteuma",
    "Kassa – keskimääräinen kk-muutos",
    "Kassa – volatiliteetti",
    "Kassa 6 kk – varovainen",
    "Kassa 6 kk – perus",
    "Kassa 6 kk – optimistinen",
]

st.caption("Näytetään viimeisin tallennettu arvo per mittari sekä trendi historiadatan perusteella.")
st.divider()

for category, metric_list in ALL_METRICS.items():
    st.markdown(f'<div class="kpi-category">{category}</div>', unsafe_allow_html=True)

    visible_metrics = [m for m in metric_list if m not in cash_detail_metrics]

    cols = st.columns(4, gap="small")
    i = 0

    for metric_name in visible_metrics:
        metric_row = latest_by_metric.get(metric_name)

        with cols[i % 4]:
            if metric_row is None:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                      <div class="kpi-title">
                        <div class="kpi-name">{metric_name}</div>
                        <div class="kpi-status">⚪</div>
                      </div>
                      <div class="kpi-value">—</div>
                      <div class="kpi-meta">Ei vielä tallennettua dataa</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                value = clean_number(metric_row["value"])
                target = clean_number(metric_row["target"])
                warning = clean_number(metric_row["warning"])
                direction = str(metric_row["direction"])

                if pd.isna(value) or pd.isna(target) or pd.isna(warning):
                    st.markdown(
                        f"""
                        <div class="kpi-card">
                          <div class="kpi-title">
                            <div class="kpi-name">{metric_name}</div>
                            <div class="kpi-status">⚪</div>
                          </div>
                          <div class="kpi-value">—</div>
                          <div class="kpi-meta">Arvoa ei voitu tulkita numeeriseksi</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    i += 1
                    continue

                status = get_status(value, target, warning, direction)

                if status == "🔴":
                    critical.append(metric_name)
                elif status == "🟡":
                    warning_list.append(metric_name)

                st.markdown(
                    f"""
                    <div class="kpi-card">
                      <div class="kpi-title">
                        <div class="kpi-name">{metric_name}</div>
                        <div class="kpi-status">{status}</div>
                      </div>
                      <div class="kpi-value">{fmt_value(metric_name, value)}</div>
                      <div class="kpi-meta">
                        Tavoite: {fmt_value(metric_name, target)}
                        &nbsp;|&nbsp;
                        Varoitus: {fmt_value(metric_name, warning)}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if metric_name == "Kassatilanne + ennuste":
                    latest_cash_rows = {}
                    for detail_metric in cash_detail_metrics:
                        latest_cash_rows[detail_metric] = latest_by_metric.get(detail_metric)

                    def get_detail_value(name):
                        row = latest_cash_rows.get(name)
                        if row is None:
                            return "—"
                        return fmt_value(name, row["value"])

                    st.markdown(
                        f"""
                        <div class="kpi-card" style="margin-top:-0.35rem;">
                          <div class="forecast-title">Kassaennuste (Excelistä syötetty)</div>
                          <div class="kpi-meta"><strong>Viimeisin toteuma:</strong> {get_detail_value("Kassa – viimeisin toteuma")}</div>
                          <div class="kpi-meta"><strong>Keskimääräinen kk-muutos:</strong> {get_detail_value("Kassa – keskimääräinen kk-muutos")}</div>
                          <div class="kpi-meta"><strong>Volatiliteetti:</strong> {get_detail_value("Kassa – volatiliteetti")}</div>
                          <div class="kpi-meta" style="margin-top:0.35rem;"><strong>6 kk ennuste</strong></div>
                          <div class="kpi-meta">Varovainen: {get_detail_value("Kassa 6 kk – varovainen")}</div>
                          <div class="kpi-meta">Perus: {get_detail_value("Kassa 6 kk – perus")}</div>
                          <div class="kpi-meta">Optimistinen: {get_detail_value("Kassa 6 kk – optimistinen")}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                trend_raw = data[data["metric"] == metric_name].copy()
                trend_data = prepare_time_series(trend_raw)

                if len(trend_data) > 1:
                    fig = px.line(trend_data, x="date_clean", y="value")
                    fig.update_traces(line_width=2)
                    fig.update_layout(
                        height=140,
                        margin=dict(l=0, r=0, t=0, b=0),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#f2f2f2"),
                        xaxis=dict(showgrid=False, zeroline=False, title=None),
                        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False, title=None),
                    )
                    st.plotly_chart(fig, use_container_width=True)

        i += 1

    st.divider()

st.markdown("## Tilanne nyt")
c1, c2, c3 = st.columns([1, 1, 3], gap="small")

with c1:
    st.markdown(
        f"""
        <div class="risk-box">
          <div style="font-weight:800;">🔴 Kriittiset</div>
          <div style="font-size:1.4rem; font-weight:900; color: var(--gold2);">{len(critical)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="risk-box">
          <div style="font-weight:800;">🟡 Varoitukset</div>
          <div style="font-size:1.4rem; font-weight:900; color: var(--gold2);">{len(warning_list)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div class="risk-box">
          <div style="font-weight:800;">Huomio</div>
          <div style="color: var(--muted);">
            Board View on vain luku. Päivitykset tehdään Ylläpito-sivulla ja kassan ennuste tuodaan Excelistä käsin.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

st.header("Poikkeamat")
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔴 Kriittiset")
    if critical:
        for m in critical:
            st.write(f"- {m}")
    else:
        st.write("Ei kriittisiä mittareita.")

with col2:
    st.subheader("🟡 Varoitusalueella")
    if warning_list:
        for m in warning_list:
            st.write(f"- {m}")
    else:
        st.write("Ei varoitusalueella olevia mittareita.")
