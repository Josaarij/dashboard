import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("Hallituksen strategiset mittarit")

# --- Sivupalkki arvojen syöttöön ---
st.sidebar.header("Päivitä mittarit")

# ELINVOIMA
pelaajamaara = st.sidebar.number_input("Pelaajamäärä yht.", value=850)
nettokasvu = st.sidebar.number_input("Nettokasvu", value=25)
lopettamis = st.sidebar.slider("Lopettamis-% (13–15v)", 0, 30, 12)
tyttopelaajat = st.sidebar.number_input("Tyttö-/naispelaajamäärä", value=220)

# TALOUS
kassa = st.sidebar.number_input("Kassatilanne (€)", value=150000)
tulosennuste = st.sidebar.number_input("Tulosennuste (€)", value=12000)
kattavuus = st.sidebar.slider("Kattavuus %", 0, 150, 102)
muut_tuotot = st.sidebar.number_input("Muut tuotot (€)", value=35000)

# VALMENNUS
pysyvyys = st.sidebar.slider("Valmentajien pysyvyys %", 0, 100, 85)
koulutetut = st.sidebar.slider("Koulutetut %", 0, 100, 72)
valmentajat_joukkue = st.sidebar.number_input("Valmentajamäärä/joukkue", value=2.1)

# LAATU
pelaajatyytyvaisyys = st.sidebar.slider("Pelaajatyytyväisyys (1–5)", 1.0, 5.0, 4.2)
vanhemmatyytyvaisyys = st.sidebar.slider("Vanhempien tyytyväisyys (1–5)", 1.0, 5.0, 4.0)
valmentajatyytyvaisyys = st.sidebar.slider("Valmentajien tyytyväisyys (1–5)", 1.0, 5.0, 4.3)
huipulle = st.sidebar.number_input("Huipputasolle nousseet/vuosi", value=3)
valmennuslinja = st.sidebar.slider("Valmennuslinjan toteutuminen %", 0, 100, 78)

# --- KPI-korttien värit ---
def vari(arvo, hyva, varoitus):
    if arvo >= hyva:
        return "green"
    elif arvo >= varoitus:
        return "orange"
    else:
        return "red"

# --- Layout ---
col1, col2 = st.columns(2)

with col1:
    st.header("🟢 ELINVOIMA")
    st.metric("Pelaajamäärä", pelaajamaara, nettokasvu)
    st.progress(tyttopelaajat / pelaajamaara)
    st.write(f"Lopettamis-%: {lopettamis}%")

    st.header("🎯 VALMENNUS")
    st.progress(pysyvyys/100, text=f"Pysyvyys {pysyvyys}%")
    st.progress(koulutetut/100, text=f"Koulutetut {koulutetut}%")
    st.metric("Valmentajaa/joukkue", valmentajat_joukkue)

with col2:
    st.header("💶 TALOUS")
    st.metric("Kassatilanne", f"{kassa:,.0f} €")
    st.metric("Tulosennuste", f"{tulosennuste:,.0f} €")
    st.progress(kattavuus/150, text=f"Kattavuus {kattavuus}%")
    st.metric("Muut tuotot", f"{muut_tuotot:,.0f} €")

    st.header("⭐ LAATU")
    st.metric("Pelaajatyytyväisyys", pelaajatyytyvaisyys)
    st.metric("Vanhempien tyyty.", vanhemmatyytyvaisyys)
    st.metric("Valmentajien tyyty.", valmentajatyytyvaisyys)
    st.metric("Huipulle/vuosi", huipulle)
    st.progress(valmennuslinja/100, text=f"Valmennuslinja {valmennuslinja}%")
