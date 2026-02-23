import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

st.set_page_config(layout="wide")
st.title("Hallituksen strateginen tilannekuva")

# --- Supabase yhteys ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Statuslogiikka ---
def get_status(value, target, warning, direction):
ALL_METRICS = {
    "ELINVOIMA": [
        "Pelaajamäärä yht.",
        "Nettokasvu",
        "Lopettamis-% 13–15v",
        "Tyttö-/naispelaajamäärä"
    ],
    "TALOUS": [
        "Kassatilanne + ennuste",
        "Tulosennuste",
        "Kattavuus %",
        "Muut tuotot"
    ],
    "VALMENNUS": [
        "Valmentajien pysyvyys",
        "Koulutetut %",
        "Valmentajamäärä/joukkue"
    ],
    "LAATU": [
        "Pelaajatyytyväisyys",
        "Vanhempien tyytyväisyys",
        "Valmentajien/taustojen tyytyväisyys",
        "Huipputasolle nousseet/vuosi",
        "Valmennuslinjan toteutuminen"
    ]
}
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

# --- Hae data ---
response = supabase.table("kpi_snapshots").select("*").execute()
data = pd.DataFrame(response.data)

if data.empty:
    st.warning("Ei tallennettua dataa.")
    st.stop()

# --- Uusin snapshot per mittari ---
latest = (
    data.sort_values("date")
        .groupby("metric")
        .tail(1)
)

# --- Riskilistat ---
critical = []
warning_list = []

st.divider()

cols = st.columns(2)
i = 0

for category, metric_list in ALL_METRICS.items():

    st.header(category)
    cols = st.columns(2)

    i = 0

    for metric_name in metric_list:

        metric_data = latest[latest["metric"] == metric_name]

        with cols[i % 2]:

            if not metric_data.empty:
                row = metric_data.iloc[0]
                status = get_status(
                    row["value"],
                    row["target"],
                    row["warning"],
                    row["direction"]
                )

                st.subheader(f"{status} {metric_name}")
                st.metric("Nykytila", row["value"])
                st.caption(f"Tavoite: {row['target']} | Varoitus: {row['warning']}")

                trend_data = data[data["metric"] == metric_name]
                if len(trend_data) > 1:
                    fig = px.line(trend_data, x="date", y="value")
                    fig.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)

            else:
                st.subheader(f"⚪ {metric_name}")
                st.caption("Ei vielä tallennettua dataa")

        i += 1

    st.divider()

st.header("Poikkeamat")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔴 Kriittiset")
    if critical:
        for m in critical:
            st.write(f"- {m}")
    else:
        st.write("Ei kriittisiä mittareita")

with col2:
    st.subheader("🟡 Varoitusalueella")
    if warning_list:
        for m in warning_list:
            st.write(f"- {m}")
    else:
        st.write("Ei varoitusalueella olevia mittareita")
