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

for _, row in latest.iterrows():
    status = get_status(row["value"], row["target"], row["warning"], row["direction"])

    if status == "🔴":
        critical.append(row["metric"])
    elif status == "🟡":
        warning_list.append(row["metric"])

    with cols[i % 2]:
        st.subheader(f"{status} {row['metric']}")
        st.metric("Nykytila", row["value"])
        st.caption(f"Tavoite: {row['target']} | Varoitus: {row['warning']}")

        trend_data = data[data["metric"] == row["metric"]]
        if len(trend_data) > 1:
            fig = px.line(trend_data, x="date", y="value")
            fig.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)

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
