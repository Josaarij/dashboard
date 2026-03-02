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
    st.header(category)
    cols = st.columns(2)
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

                st.subheader(f"{status} {metric_name}")
                st.metric("Nykytila", row["value"])
                st.caption(f"Tavoite: {row['target']} | Varoitus: {row['warning']}")

                trend_data = data[data["metric"] == metric_name].sort_values("date")

                # Näytä trendi jos historiassa on useampi piste
                if len(trend_data) > 1:
                    fig = px.line(trend_data, x="date", y="value")
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
