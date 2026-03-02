import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

st.set_page_config(layout="wide")
st.title("Hallituksen strateginen tilannekuva")

# --- Teema: musta-kulta + tiivis board view ---
st.markdown(
    """
    <style>
      :root{
        --bg: #0b0b0b;
        --panel: #111111;
        --panel2: #0f0f0f;
        --text: #f2f2f2;
        --muted: #b7b7b7;
        --gold: #caa64a;
        --gold2:#e1c36b;
        --border: rgba(202,166,74,0.22);
      }

      /* App tausta */
      .stApp{
        background: radial-gradient(1200px 800px at 15% 10%, #161616 0%, var(--bg) 55%, #070707 100%);
        color: var(--text);
      }

      /* Otsikot ja teksti hieman pienemmäksi */
      h1 { font-size: 1.55rem !important; letter-spacing: .3px; }
      h2 { font-size: 1.20rem !important; margin-top: .25rem !important; }
      h3 { font-size: 1.05rem !important; }
      p, li, span, div { font-size: 0.95rem; }

      /* Streamlit default padding tiiviimmäksi */
      .block-container { padding-top: 1.0rem; padding-bottom: 1.0rem; }
      hr { border-color: rgba(255,255,255,0.08) !important; }

      /* Kategorian header -viimeistely */
      .kpi-category{
        margin: 0.25rem 0 0.25rem 0;
        padding: .35rem .65rem;
        border-left: 4px solid var(--gold);
        background: linear-gradient(90deg, rgba(202,166,74,0.12), rgba(202,166,74,0.02));
        border-radius: 10px;
        font-weight: 700;
        letter-spacing: .4px;
      }

      /* KPI-kortti */
      .kpi-card{
        background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: .65rem .75rem .55rem .75rem;
        box-shadow: 0 10px 24px rgba(0,0,0,0.30);
        margin-bottom: .75rem;
      }

      .kpi-title{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:.6rem;
        margin-bottom:.20rem;
      }
      .kpi-name{
        font-weight: 750;
        letter-spacing:.2px;
        color: var(--text);
        font-size: 0.98rem;
        line-height: 1.15rem;
      }
      .kpi-status{
        font-size: 1.15rem;
        filter: drop-shadow(0 1px 1px rgba(0,0,0,0.35));
      }

      .kpi-value{
        font-size: 1.35rem;
        font-weight: 850;
        color: var(--gold2);
        line-height: 1.4rem;
        margin: .15rem 0 .25rem 0;
      }
      .kpi-meta{
        color: var(--muted);
        font-size: 0.82rem;
        margin-bottom: .35rem;
      }

      /* Plotly chart: tumma tausta */
      .js-plotly-plot, .plot-container { background: transparent !important; }

      /* Streamlit metric-komponentti pienemmäksi (jos jää käyttöön) */
      [data-testid="stMetricValue"]{ font-size: 1.35rem !important; }
      [data-testid="stMetricLabel"]{ font-size: .85rem !important; color: var(--muted) !important; }

      /* Poikkeamat-paneelit */
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
def get_status(value, target, warning, direction):
    if direction == "up":
        if value >= target:
            return "🟢"
        elif value >= warning:
            return "🟡"
        else:
            return "🔴"
    else:
        if value <= target:
            return "🟢"
        elif value <= warning:
            return "🟡"
        else:
            return "🔴"


from metrics_definitions import ALL_METRICS

# --- Hae data ---
response = supabase.table("kpi_snapshots").select("*").execute()
data = pd.DataFrame(response.data)

if data.empty:
    st.warning("Ei tallennettua dataa.")
    st.stop()

# Varmista oikeat tyypit (Supabase palauttaa usein date-stringinä)
data["date"] = pd.to_datetime(data["date"], errors="coerce")
with st.expander("DEBUG: mittarinimet ja viimeisimmät rivit", expanded=False):
    st.write("Tietokannassa olevat metric-nimet:")
    st.dataframe(pd.DataFrame(sorted(data["metric"].dropna().unique()), columns=["metric"]))

    target_metric = "Tyttö-/naispelaajamäärä"
    st.write(f"Viimeisimmät rivit mittarille: {target_metric}")
    st.dataframe(
        data[data["metric"] == target_metric]
        .sort_values("date", ascending=False)
        .head(10),
        use_container_width=True
    )
# --- Uusin snapshot per mittari ---
latest = (
    data.sort_values("date")
    .groupby("metric", as_index=False)
    .tail(1)
)

# --- Riskilistat ---
critical = []
warning_list = []

st.caption("Näytetään viimeisin tallennettu arvo per mittari sekä trendi historiadatan perusteella.")
st.divider()

# --- Mittarien näyttö kategorioittain ---
for category, metric_list in ALL_METRICS.items():
    st.markdown(f'<div class="kpi-category">{category}</div>', unsafe_allow_html=True)
    cols = st.columns(4, gap="small")
    i = 0

    for metric_name in metric_list:
        metric_data = latest[latest["metric"] == metric_name]

        with cols[i % 2]:
            if not metric_data.empty:
                row = metric_data.iloc[0]

                status = get_status(
                    float(row["value"]),
                    float(row["target"]),
                    float(row["warning"]),
                    str(row["direction"]),
                )

                if status == "🔴":
                    critical.append(metric_name)
                elif status == "🟡":
                    warning_list.append(metric_name)

               # Arvojen muotoilu (valinnainen: tee rahasta/ prosentista siisti)
val = row["value"]
target = row["target"]
warning = row["warning"]

st.markdown(
    f"""
    <div class="kpi-card">
      <div class="kpi-title">
        <div class="kpi-name">{metric_name}</div>
        <div class="kpi-status">{status}</div>
      </div>
      <div class="kpi-value">{val}</div>
      <div class="kpi-meta">Tavoite: {target} &nbsp;|&nbsp; Varoitus: {warning}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

                # Näytä trendi jos historiassa on useampi piste
                if len(trend_data) > 1:
                    fig = px.line(trend_data, x="date", y="value")
                    fig.update_traces(line_width=2)
fig.update_layout(
    height=140,  # pienempi kuin ennen
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f2f2f2"),
    xaxis=dict(showgrid=False, zeroline=False, title=None),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False, title=None),
)
                    fig.update_layout(
                        height=220,
                        margin=dict(l=0, r=0, t=10, b=0),
                        xaxis_title=None,
                        yaxis_title=None,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Ei vielä trendiä (vain yksi tallennus).")
            else:
                st.subheader(f"⚪ {metric_name}")
                st.caption("Ei vielä tallennettua dataa tälle mittarille.")

        i += 1

    st.divider()

# --- Poikkeamat ---
st.markdown("## Tilanne nyt")
c1, c2, c3 = st.columns([1,1,3], gap="small")

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
            Näkymä näyttää viimeisimmän tallennetun arvon per mittari ja trendin historiasta.
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
