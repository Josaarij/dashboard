import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Ylläpito – mittarien päivitys")

# --- Supabase yhteys ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Statuslogiikka (vain esikatselua varten) ---
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


# --- Mittarit (kiinteästi hallituksen päättämät) ---
ALL_METRICS = {
    "ELINVOIMA": [
        "Pelaajamäärä yht.",
        "Nettokasvu (uudet–lopettaneet)",
        "Lopettamis-% 13–15v",
        "Tyttö-/naispelaajamäärä",
    ],
    "TALOUS": [
        "Kassatilanne + ennuste",
        "Tulosennuste",
        "Kattavuus % (maksut/kulut)",
        "Muut tuotot",
    ],
    "VALMENNUS": [
        "Valmentajien pysyvyys",
        "Koulutetut %",
        "Valmentajamäärä/joukkue",
    ],
    "LAATU": [
        "Pelaajatyytyväisyys",
        "Vanhempien tyytyväisyys",
        "Valmentajien/taustojen tyytyväisyys",
        "Huipputasolle nousseet/vuosi",
        "Valmennuslinjan toteutuminen",
    ],
}

# --- Oletusarvot (voit muokata myöhemmin) ---
DEFAULTS = {
    "Pelaajamäärä yht.": {"value": 850, "target": 900, "warning": 820, "direction": "up"},
    "Nettokasvu (uudet–lopettaneet)": {"value": 25, "target": 30, "warning": 10, "direction": "up"},
    "Lopettamis-% 13–15v": {"value": 12, "target": 10, "warning": 15, "direction": "down"},
    "Tyttö-/naispelaajamäärä": {"value": 220, "target": 250, "warning": 200, "direction": "up"},

    "Kassatilanne + ennuste": {"value": 150000, "target": 100000, "warning": 60000, "direction": "up"},
    "Tulosennuste": {"value": 12000, "target": 0, "warning": -20000, "direction": "up"},
    "Kattavuus % (maksut/kulut)": {"value": 102, "target": 100, "warning": 95, "direction": "up"},
    "Muut tuotot": {"value": 35000, "target": 30000, "warning": 20000, "direction": "up"},

    "Valmentajien pysyvyys": {"value": 85, "target": 90, "warning": 75, "direction": "up"},
    "Koulutetut %": {"value": 72, "target": 80, "warning": 60, "direction": "up"},
    "Valmentajamäärä/joukkue": {"value": 2.1, "target": 2.0, "warning": 1.5, "direction": "up"},

    "Pelaajatyytyväisyys": {"value": 4.2, "target": 4.3, "warning": 4.0, "direction": "up"},
    "Vanhempien tyytyväisyys": {"value": 4.0, "target": 4.2, "warning": 3.9, "direction": "up"},
    "Valmentajien/taustojen tyytyväisyys": {"value": 4.3, "target": 4.4, "warning": 4.0, "direction": "up"},
    "Huipputasolle nousseet/vuosi": {"value": 3, "target": 3, "warning": 1, "direction": "up"},
    "Valmennuslinjan toteutuminen": {"value": 78, "target": 85, "warning": 70, "direction": "up"},
}

# --- Hae viimeisimmät arvot (esitäytetään lomake, jos löytyy) ---
resp = supabase.table("kpi_snapshots").select("*").execute()
hist = pd.DataFrame(resp.data)

latest_by_metric = {}
if not hist.empty:
    hist["date"] = pd.to_datetime(hist["date"], errors="coerce")
    latest = (
        hist.sort_values("date")
            .groupby("metric", as_index=False)
            .tail(1)
    )
    for _, r in latest.iterrows():
        latest_by_metric[str(r["metric"])] = {
            "value": float(r["value"]),
            "target": float(r["target"]),
            "warning": float(r["warning"]),
            "direction": str(r["direction"]),
        }

st.caption("Syötä arvot ja rajat. Lopuksi tallenna snapshot. Tallennus tekee yhden rivin per mittari Supabaseen.")
st.divider()

# --- Lomake: kaikki mittarit ---
metrics = {}  # <-- tämä on se muuttuja, jonka puuttuminen aiheutti sinun virheen

with st.form("kpi_form"):
    for category, metric_list in ALL_METRICS.items():
        st.subheader(category)

        for metric_name in metric_list:
            # Esitäyttö: ensisijaisesti tietokannan viimeisin, muuten DEFAULTS, muuten 0
            seed = latest_by_metric.get(metric_name) or DEFAULTS.get(metric_name) or {
                "value": 0.0, "target": 0.0, "warning": 0.0, "direction": "up"
            }

            c1, c2, c3, c4 = st.columns([2.2, 1, 1, 1.2])

            with c1:
                value = st.number_input(
                    f"{metric_name} – arvo",
                    value=float(seed["value"]),
                    key=f"{metric_name}_value",
                )
            with c2:
                target = st.number_input(
                    "Tavoite",
                    value=float(seed["target"]),
                    key=f"{metric_name}_target",
                )
            with c3:
                warning = st.number_input(
                    "Varoitusraja",
                    value=float(seed["warning"]),
                    key=f"{metric_name}_warning",
                )
            with c4:
                direction_ui = st.selectbox(
                    "Suunta",
                    ["up (suurempi parempi)", "down (pienempi parempi)"],
                    index=0 if seed["direction"] == "up" else 1,
                    key=f"{metric_name}_direction",
                )
                direction = "up" if direction_ui.startswith("up") else "down"

            metrics[metric_name] = (value, target, warning, direction)

        st.divider()

    submitted = st.form_submit_button("Tallenna snapshot tietokantaan")

# --- Tallennus ---
if submitted:
    now_iso = datetime.now().isoformat()

    rows = []
    for name, (value, target, warning, direction) in metrics.items():
        rows.append({
            "date": now_iso,
            "metric": name,
            "value": float(value),
            "target": float(target),
            "warning": float(warning),
            "direction": direction,
        })

    supabase.table("kpi_snapshots").insert(rows).execute()
    st.success("Snapshot tallennettu Supabaseen (yksi rivi per mittari).")

# --- Esikatselu: statuslista ---
st.divider()
st.subheader("Esikatselu (status nykyisillä syötöillä)")

preview_rows = []
for name, (value, target, warning, direction) in metrics.items():
    status = get_status(float(value), float(target), float(warning), direction)
    preview_rows.append({
        "Status": status,
        "Mittari": name,
        "Arvo": value,
        "Tavoite": target,
        "Varoitus": warning,
        "Suunta": direction,
    })

st.dataframe(pd.DataFrame(preview_rows), use_container_width=True)
