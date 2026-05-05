import streamlit as st
import pandas as pd
import altair as alt
import folium
import gpxpy
from data import load_data, load_flights
import base64
import os
import requests
from datetime import datetime, timedelta

# =========================
# 💱 EXCHANGE RATE (LIVE)
# =========================
@st.cache_data(ttl=3600)
def get_chf_to_eur():
    try:
        url = "https://api.exchangerate.host/latest?base=CHF&symbols=EUR"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data["rates"]["EUR"]
    except:
        return 1.04  # fallback

@st.cache_data(ttl=3600)
def get_chf_eur_history():
    end = datetime.today()
    start = end - timedelta(days=7)

    url = (
        f"https://api.exchangerate.host/timeseries"
        f"?start_date={start.strftime('%Y-%m-%d')}"
        f"&end_date={end.strftime('%Y-%m-%d')}"
        f"&base=CHF&symbols=EUR"
    )

    try:
        res = requests.get(url, timeout=5)
        data = res.json()

        rates = data["rates"]

        df_rates = pd.DataFrame([
            {"date": d, "rate": v["EUR"]}
            for d, v in rates.items()
        ])

        df_rates["date"] = pd.to_datetime(df_rates["date"])
        df_rates = df_rates.sort_values("date")

        return df_rates

    except:
        return None


def plot_exchange_rate(df_rates):
    return alt.Chart(df_rates).mark_line(point=True).encode(
        x=alt.X("date:T", title=""),
        y=alt.Y("rate:Q", title="CHF→EUR"),
        tooltip=["date:T", "rate:Q"]
    ).properties(height=150)


# =========================
# 🔧 CONFIG
# =========================
GPX_FOLDER = "gpx_files"

st.set_page_config(layout="wide")

# =========================
# 📂 HELPERS
# =========================
def get_base64(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def convert_to_eur(row):
    if row["currency"] == "CHF":
        return row["cost"] * CHF_TO_EUR
    return row["cost"]

def get_gpx_file_for_day(day):
    if day == 1:
        return os.path.join(GPX_FOLDER, "tmr.gpx")
    else:
        return os.path.join(GPX_FOLDER, f"day{day-1}.gpx")  # FIXED


# =========================
# 📊 DATA
# =========================
df = load_data()
flights = load_flights()

CHF_TO_EUR = get_chf_to_eur()  # ✅ USE LIVE RATE

if "day" not in st.session_state:
    st.session_state.day = int(df["day"].min())

df["cost_eur"] = df.apply(convert_to_eur, axis=1)
total_eur = df["cost_eur"].sum()

# =========================
# 🎨 HERO
# =========================
img_base64 = get_base64("mat.jpg")

st.markdown(f"""
<style>
.hero {{
    background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)),
    url("data:image/jpg;base64,{img_base64}");
    background-size: cover;
    background-position: 50% 10%;
    padding: 100px;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
}}
</style>

<div class="hero">
    <h1>🏔️ Monte Rosa Tour</h1>
</div>
""", unsafe_allow_html=True)

# =========================
# 🔗 LINKS
# =========================
wikiloc_url = "https://el.wikiloc.com/oreibasia-diadromes/tmr-reduced-6-days-itinerary-254794250"

# =========================
# 📌 SIDEBAR
# =========================
st.sidebar.title("🏔️ Monte Rosa Tour")

day = st.sidebar.selectbox(
    "Select Day",
    df["day"],
    index=list(df["day"]).index(st.session_state.day)
)

st.session_state.day = day

progress = day / df["day"].max()
st.sidebar.progress(progress)

# 💱 CURRENT RATE
st.sidebar.metric("CHF → EUR", f"{CHF_TO_EUR:.2f}")

# 📈 HISTORY
rates_df = get_chf_eur_history()

if rates_df is not None:
    st.sidebar.caption("Last 7 days")
    st.sidebar.altair_chart(plot_exchange_rate(rates_df), use_container_width=True)
else:
    st.sidebar.caption("No exchange data")

st.sidebar.markdown("---")
st.sidebar.markdown(f"[🗺️ Wikiloc Route]({wikiloc_url})")

# =========================
# 📑 TABS
# =========================
tab1, tab2 = st.tabs(["🏔️ Daily Plan", "🚆 Transport"])

# =========================
# 🏔️ TAB 1
# =========================
with tab1:

    col_prev, _, col_next = st.columns([1,2,1])

    with col_prev:
        if st.button("⬅️ Previous", use_container_width=True):
            if st.session_state.day > df["day"].min():
                st.session_state.day -= 1
                st.rerun()

    with col_next:
        if st.button("Next ➡️", use_container_width=True):
            if st.session_state.day < df["day"].max():
                st.session_state.day += 1
                st.rerun()

    st.markdown("<script>window.scrollTo(0,0);</script>", unsafe_allow_html=True)

    row = df[df["day"] == day].iloc[0]

    st.title(f"Day {row['day']}: {row['from']} → {row['to']}")
    st.caption(row["date"])

    # --- METRICS
    col1, col2, col3 = st.columns(3)
    col1.metric("Distance", f"{row['distance_km']} km" if pd.notna(row['distance_km']) else "-")
    col2.metric("Elevation ↑", f"{row['elevation_up']} m" if pd.notna(row['elevation_up']) else "-")
    col3.metric("Time", f"{row['time_h']} h" if pd.notna(row['time_h']) else "-")

    # --- STAY
    st.subheader("🏠 Accommodation")
    st.write(f"**{row['stay']}**")
    st.write(f"💰 {row['cost']} {row['currency']}")

    # --- FLIGHTS IN DAY VIEW
    if row["day"] == 1:
        f = flights[0]
        st.info(f"✈️ {f['from']} → {f['to']} | {f['date']} {f['time']} | {f['flight']}")

    if row["day"] == df["day"].max():
        f = flights[1]
        st.info(f"✈️ {f['from']} → {f['to']} | {f['date']} {f['time']} | {f['flight']}")

    # --- SUMMARY
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Distance", f"{round(df['distance_km'].sum(skipna=True),1)} km")
    col2.metric("Elevation ↑", f"{int(df['elevation_up'].sum(skipna=True))} m")
    col3.metric("Cost / person", f"{int(total_eur/6)} €")

    # --- MAP
    st.markdown("---")
    st.subheader("🗺️ Route Map")

    gpx_path = get_gpx_file_for_day(day)

    if os.path.exists(gpx_path):
        with open(gpx_path, "r", encoding="utf-8") as f:
            gpx = gpxpy.parse(f)

        points = [(p.latitude, p.longitude)
                  for t in gpx.tracks
                  for s in t.segments
                  for p in s.points]

        if points:
            m = folium.Map()
            folium.PolyLine(points).add_to(m)
            m.fit_bounds(points)
            st.components.v1.html(m._repr_html_(), height=400)

# =========================
# 🚆 TAB 2
# =========================
with tab2:

    st.title("🚆 Transport")

    with st.expander("✈️ Flights"):
        for f in flights:
            st.markdown(f"""
            **{f['type']}**  
            {f['from']} → {f['to']}  
            🕒 {f['date']} {f['time']}  
            ✈️ {f['flight']}
            """)
            st.markdown("---")

    st.markdown("### 🧠 Tips")
    st.markdown("- Be early\n- Check buses\n- Offline tickets")