import streamlit as st
import pandas as pd
import altair as alt
import folium
import gpxpy
from data import load_data, load_flights
import base64
import os

# =========================
# 🔧 CONFIG
# =========================
CHF_TO_EUR = 1.04
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
    """
    Day logic:
    Day 1 -> full route
    Day 2 -> day1.gpx
    Day 3 -> day2.gpx
    ...
    """
    if day == 1:
        return os.path.join(GPX_FOLDER, "tmr.gpx")
    else:
        return os.path.join(GPX_FOLDER, f"d{day-1}.gpx")

# =========================
# 📊 DATA
# =========================
df = load_data()
flights = load_flights()

if "day" not in st.session_state:
    st.session_state.day = int(df["day"].min())

df["cost_eur"] = df.apply(convert_to_eur, axis=1)
total_eur = df["cost_eur"].sum()

# =========================
# 🎨 HERO IMAGE
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

@media (max-width: 768px) {{
    .hero {{
        padding: 60px;
        background-position: 50% 5%;
    }}
}}
</style>

<div class="hero">
    <h1>🏔️ Monte Rosa Tour</h1>
    <p>Adventure awaits</p>
</div>
""", unsafe_allow_html=True)


# =========================
# 🔗 LINKS
# =========================
wikiloc_url = "https://el.wikiloc.com/oreibasia-diadromes/tmr-reduced-6-days-itinerary-254794250?h=xpqqvvg3pk&wa=sd&utm_campaign=badge&utm_source=unknown&utm_medium=unknown"

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

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Route")
st.sidebar.markdown(f"[🔗 Wikiloc Trail]({wikiloc_url})")

st.sidebar.markdown("### 🚀 Quick Links")
st.sidebar.markdown("[🚌 Bus](https://www.comazzibus.com/)")
st.sidebar.markdown("[🚆 Trenitalia](https://www.trenitalia.com/)")
st.sidebar.markdown("[🚆 SBB](https://www.sbb.ch/)")

# =========================
# 📑 TABS
# =========================
tab1, tab2 = st.tabs(["🏔️ Daily Plan", "🚆 Transport Info"])

# =========================
# 🏔️ TAB 1
# =========================
col_prev, _, col_next = st.columns([1,2,1])

with col_prev:
    if st.button("⬅️ Previous", use_container_width=True):
        if st.session_state.day > df["day"].min():
            st.session_state.day -= 1

with col_next:
    if st.button("Next ➡️", use_container_width=True):
        if st.session_state.day < df["day"].max():
            st.session_state.day += 1

day = st.session_state.day

with tab1:
    row = df[df["day"] == day].iloc[0]

    st.title(f"Day {row['day']}: {row['from']} → {row['to']}")
    st.caption(row["date"])

    st.markdown(f"[🗺️ Full Route]({wikiloc_url})")

    # --- Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Distance", f"{row['distance_km']} km" if pd.notna(row['distance_km']) else "-")
    col2.metric("Elevation ↑", f"{row['elevation_up']} m" if pd.notna(row['elevation_up']) else "-")
    col3.metric("Time", f"{row['time_h']} h" if pd.notna(row['time_h']) else "-")

    # --- Stay ---
    st.subheader("🏠 Accommodation")
    st.write(f"**{row['stay']}**")
    st.write(f"💰 {row['cost']} {row['currency']}")

    if row.get("link"):
        st.markdown(f"[🔗 Open booking]({row['link']})")

    if row["notes"]:
        st.subheader("⚠️ Notes")
        st.markdown(row["notes"])

    if row["day"] == 1:
        st.subheader("✈️ Flight to Milan")

        departure = flights[0]

        st.info(f"""
        {departure['from']} → {departure['to']}  
        🕒 {departure['date']} at {departure['time']}  
        ✈️ Flight {departure['flight']}
        """)
    if row["day"] == df["day"].max():
        st.subheader("✈️ Return Flight")

        return_flight = flights[1]

        st.info(f"""
        {return_flight['from']} → {return_flight['to']}  
        🕒 {return_flight['date']} at {return_flight['time']}  
        ✈️ Flight {return_flight['flight']}
        """)
    # =========================
    # 📊 SUMMARY
    # =========================
    st.markdown("---")
    st.subheader("📊 Trip Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Distance", f"{round(df['distance_km'].sum(skipna=True),1)} km")
    col2.metric("Elevation ↑", f"{int(df['elevation_up'].sum(skipna=True))} m")
    col3.metric("Cost / person", f"{int(total_eur/6)} €")

    # =========================
    # 📈 CHART
    # =========================
    st.subheader("📈 Elevation per Day")

    df["elevation_down_neg"] = -df["elevation_down"].fillna(0)

    chart_df = df.melt(
        id_vars="day",
        value_vars=["elevation_up", "elevation_down_neg"],
        var_name="type",
        value_name="meters"
    )

    chart = alt.Chart(chart_df).mark_bar().encode(
        x="day:O",
        y="meters:Q",
        color="type:N",
        tooltip=["day", "type", "meters"]
    )

    st.altair_chart(chart, use_container_width=True)

    # =========================
    # 🗺️ MAP
    # =========================
    st.markdown("---")
    st.subheader("🗺️ Route Map")

    gpx_path = get_gpx_file_for_day(day)

    if os.path.exists(gpx_path):
        with open(gpx_path, "r", encoding="utf-8") as f:
            gpx = gpxpy.parse(f)

        points = [
            (p.latitude, p.longitude)
            for track in gpx.tracks
            for segment in track.segments
            for p in segment.points
        ]

        if points:
            m = folium.Map()
            folium.PolyLine(points, color="blue", weight=4).add_to(m)
            m.fit_bounds(points)

            folium.Marker(points[0], tooltip="Start").add_to(m)
            folium.Marker(points[-1], tooltip="End").add_to(m)

            st.components.v1.html(m._repr_html_(), height=400)
        else:
            st.warning("GPX file has no points.")

    else:
        st.info(f"No GPX file found: {gpx_path}")

# =========================
# 🚆 TAB 2
# =========================
with tab2:
    st.title("🚆 Transport")

    with st.expander("✈️ Flights"):
        for f in flights:
            col1, col2, col3 = st.columns(3)

            col1.metric("Route", f"{f['from']} → {f['to']}")
            col2.metric("Date & Time", f"{f['date']} | {f['time']}")
            col3.metric("Flight", f["flight"])

            st.markdown("---")

    with st.expander("🚆 Train"):
        st.write("Milano → Domodossola")

    with st.expander("🚌 Bus"):
        st.write("Domodossola → Macugnaga")

    with st.expander("🇨🇭 Switzerland"):
        st.write("Zermatt / Brig transport")

    st.markdown("---")
    st.markdown("### 🧠 Tips")
    st.markdown("""
    - Be early  
    - Check last buses  
    - Offline tickets  
    """)