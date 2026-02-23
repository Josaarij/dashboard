import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Hallituksen strateginen mittaristo")

DATA_PATH = "data/history.csv"

# --- Luo datafolder jos ei ole ---
if not os.path.exists("data"):
    os.makedirs("data")

# --- Lataa historiadata turvallisesti ---
if os.path.exists(DATA_PATH) and os.path.getsize(DATA_PATH) > 0:
    try:
        history = pd.read_csv(DATA_PATH)
    except Exception:
        history = pd.DataFrame()
else:
    history = pd.DataFrame()

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

# --- Sidebar: mittarien syöttö ---
st.sidebar.header("Päivitä mittarit")

def input_metric(name, default_value=0.0):
    value = st.sidebar.number_input(f"{name} arvo", value=float(default_value))
    target = st.sidebar.number_input(f"{name} tavoite", value=float(default_value))
    warning = st.sidebar.number_input(f"{name} varoitusraja", value=float(default_value*0.8))
    direction = st.sidebar.selectbox(f"{name} suunta",
                                      ["up (suurempi parempi)", "down (pienempi parempi)"])
    direction = "up" if "up" in direction else "down"
    return value, target, warning, direction

metrics = {}

metrics["Pelaajamäärä"] = input_metric("Pelaajamäärä", 850)
metrics["Kattavuus %"] = input_metric("Kattavuus %", 100)
metrics["Valmentajien pysyvyys %"] = input_metric("Valmentajien pysyvyys %", 85)
metrics["Pelaajatyytyväisyys"] = input_metric("Pelaajatyytyväisyys", 4.2)

# --- Tallennus ---
if st.sidebar.button("Tallenna snapshot"):
    row = {"date": datetime.today().strftime("%Y-%m-%d")}
    for name, (value, _, _, _) in metrics.items():
        row[name] = value
    history = pd.concat([history, pd.DataFrame([row])], ignore_index=True)
    history.to_csv(DATA_PATH, index=False)
    st.sidebar.success("Tallennettu")

# --- Dashboard ---
st.header("Strateginen tilannekuva")

cols = st.columns(2)

i = 0
for name, (value, target, warning, direction) in metrics.items():
    status = get_status(value, target, warning, direction)

    with cols[i % 2]:
        st.subheader(f"{status} {name}")
        st.metric("Nykytila", value)
        st.write(f"Tavoite: {target} | Varoitus: {warning}")

        if not history.empty and name in history.columns:
            fig = px.line(history, x="date", y=name,
                          title=f"{name} trendi")
            st.plotly_chart(fig, use_container_width=True)

    i += 1
