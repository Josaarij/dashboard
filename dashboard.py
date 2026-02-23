import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Hallituksen strateginen mittaristo")

# --- Supabase yhteys ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Statuslogiikka ---
def get_status(value, target, warning, direction="up"):
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

# --- Hae historiadata ---
response = supabase.table("kpi_snapshots").select("*").execute()
history = pd.DataFrame(response.data)

# --- Sidebar ---
st.sidebar.header("Päivitä mittarit")

def input_metric(name, default_value):
    value = st.sidebar.number_input(f"{name} arvo", value=float(default_value))
    target = st.sidebar.number_input(f"{name} tavoite", value=float(default_value))
    warning = st.sidebar.number_input(f"{name} varoitusraja", value=float(default_value*0.8))
    direction = st.sidebar.selectbox(
        f"{name} suunta",
        ["up (suurempi parempi)", "down (pienempi parempi)"],
        key=name
    )
    direction = "up" if "up" in direction else "down"
    return value, target, warning, direction

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

# --- Tallennus ---
if st.sidebar.button("Tallenna snapshot"):
    for name, (value, target, warning, direction) in metrics.items():
        supabase.table("kpi_snapshots").insert({
            "date": datetime.now().isoformat(),
            "metric": name,
            "value": value,
            "target": target,
            "warning": warning,
            "direction": direction
        }).execute()
    st.sidebar.success("Tallennettu tietokantaan")

# --- Dashboard ---
st.header("Strateginen tilannekuva")

# Riskikooste
reds = 0
yellows = 0

cols = st.columns(2)
i = 0

for name, (value, target, warning, direction) in metrics.items():
    status = get_status(value, target, warning, direction)

    if status == "🔴":
        reds += 1
    elif status == "🟡":
        yellows += 1

    with cols[i % 2]:
        st.subheader(f"{status} {name}")
        st.metric("Nykytila", value)
        st.write(f"Tavoite: {target} | Varoitus: {warning}")

        if not history.empty:
            df_metric = history[history["metric"] == name]
            if not df_metric.empty:
                fig = px.line(df_metric, x="date", y="value", title="Trendi")
                st.plotly_chart(fig, use_container_width=True)

    i += 1

st.divider()
st.subheader("Riskikooste")

st.write(f"🔴 Kriittisiä mittareita: {reds}")
st.write(f"🟡 Varoitusalueella: {yellows}")
