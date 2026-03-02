import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

from metrics_definitions import ALL_METRICS  # yhteinen mittarilista

st.set_page_config(layout="wide")
st.title("Hallituksen strateginen tilannekuva")

# --- Teema: musta-kulta + tiivis board view ---
st.markdown(
    """
    <style>
      :root{
        --bg: #0b0b0b;
        --panel: #111111;
        --text: #f2f2f2;
        --muted: #b7b7b7;
        --gold: #caa64a;
        --gold2:#e1c36b;
        --border: rgba(202,166,74,0.22);
      }

      .stApp{
        background: radial-gradient(1200px 800px at 15% 10%, #161616 0%, var(--bg) 55%, #070707 100%);
        color: var(--text);
      }

      h1 { font-size: 1.55rem !important; letter-spacing: .3px; }
      h2 { font-size: 1.20rem !important; margin-top: .25rem !important; }
      h3 { font-size: 1.05rem !important; }
      p, li, span, div { font-size: 0.95rem; }

      .block-container { padding-top: 1.0rem; padding-bottom: 1.0rem; }
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

  /* UUSI: varmistaa ettei sisältö pursua ulos */
        overflow: hidden;
}

      .kpi-title{
        display:flex;
        align-items:center;
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
      }
      .kpi-status{
        font-size: 1.15rem;
        filter: drop-shadow(0 1px 1px rgba(0,0,0,0.35));
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
        margin-bottom: .35rem;
      }

      .js-plotly-plot, .plot-container { background: transparent !important; }

      .risk-box{
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: .65rem .75rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Supabase yhteys ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Statuslogiikka ---
def get_status(value: float, target: float, warning: float, direction: str) -> str:
    if direction == "up":
        if value >= target:
            return "🟢"
        if value >= warning:
            return "🟡"
        return "🔴"
    # direction == "down"
    if value <= target:
        return "🟢"
    if value <= warning:
        return "🟡"
    return "🔴"


def fmt_value(metric_name: str, v) -> str:
    """Kevyt muotoilu: eurot/prosentit/asteikot.
    (Tätä voi laajentaa myöhemmin, mutta nyt pidetään robustina.)
    """
    try:
        x = float(v)
    except Exception:
        return str(v)

    name = metric_name.lower()
    if "€" in metric_name or "kassa" in name or "tulos" in name or "tuotot" in name:
        # euroa, pyöristä kokonaisiin
        return f"{x:,.0f} €".replace(",", " ")
    if "%" in metric_name or " %" in metric_name or "kattavuus" in name or "pysyvyys" in name or "koulutetut" in name:
        return f"{x:.0f} %"
    if "tyytyväisyys" in name:
        return f"{x:.1f} / 5"
    if "valmentajamäärä/joukkue" in name:
        return f"{x:.1f}"
    # oletus
    if abs(x) >= 1000:
        return f"{x:,.0f}".replace(",", " ")
    return f"{x:.1f}" if x % 1 != 0 else f"{x:.0f}"


# --- Hae data ---
resp = supabase.table("kpi_snapshots").select("*").execute()
data = pd.DataFrame(resp.data)

if data.empty:
    st.warning("Ei tallennettua dataa.")
    st.stop()

data["date"] = pd.to_datetime(data["date"], errors="coerce")

# --- Uusin snapshot per mittari ---
latest = (
    data.sort_values("date")
    .groupby("metric", as_index=False)
    .tail(1)
)

# --- Riskilistat ---
critical: list[str] = []
warning_list: list[str] = []

st.caption("Näytetään viimeisin tallennettu arvo per mittari sekä trendi historiadatan perusteella.")
st.divider()

# --- Mittarien näyttö kategorioittain ---
for category, metric_list in ALL_METRICS.items():
    st.markdown(f'<div class="kpi-category">{category}</div>', unsafe_allow_html=True)

    cols = st.columns(4, gap="small")
    i = 0

    for metric_name in metric_list:
        metric_row = latest[latest["metric"] == metric_name]

        with cols[i % 4]:
            if metric_row.empty:
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
                row = metric_row.iloc[0]
                value = float(row["value"])
                target = float(row["target"])
                warning = float(row["warning"])
                direction = str(row["direction"])

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

                trend_data = data[data["metric"] == metric_name].sort_values("date")

                if len(trend_data) > 1:
                    fig = px.line(trend_data, x="date", y="value")
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

# --- Yhteenvetobanneri ---
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
            Hallitusnäkymä on vain luku. Päivitykset tehdään Ylläpito-sivulla ja tallennetaan snapshotina.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# --- Poikkeamat ---
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
