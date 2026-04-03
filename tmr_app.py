import streamlit as st
import pandas as pd
import altair as alt
import folium
import gpxpy
from data import load_data
import base64

def get_base64(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


CHF_TO_EUR = 1.04  # approx
st.set_page_config(layout="wide")

df = load_data()
def convert_to_eur(row):
    if row["currency"] == "CHF":
        return row["cost"] * CHF_TO_EUR
    return row["cost"]

df["cost_eur"] = df.apply(convert_to_eur, axis=1)
total_eur = df["cost_eur"].sum()

# ========================


img_base64 = get_base64("mat.jpg")

st.markdown(f"""
<style>
.hero {{
    background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)),
    url("data:image/jpg;base64,{img_base64}");
    background-size: cover;
    background-position: top;
    padding: 100px;
    border-radius: 15px;
    color: white;
    text-align: center;
}}

/* 📱 MOBILE */
@media (max-width: 768px) {{
    .hero {{
        background-position: top center;
        padding: 60px;
    }}
}}
</style>
""", unsafe_allow_html=True)

# =========================
# 🌐 GLOBAL LINKS
# =========================
wikiloc_url = "https://el.wikiloc.com/oreibasia-diadromes/tmr-reduced-6-days-itinerary-254794250?h=xpqqvvg3pk&wa=sd&utm_campaign=badge&utm_source=unknown&utm_medium=unknown"

# =========================
# 📌 SIDEBAR
# =========================
st.sidebar.title("🏔️ Monte Rosa Tour")

day = st.sidebar.selectbox("Select Day", df["day"])

progress = day / df["day"].max()
st.sidebar.progress(progress)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Route")
st.sidebar.markdown(f"[🔗 Wikiloc Trail]({wikiloc_url})")

st.sidebar.markdown("### 🚀 Quick Links")
st.sidebar.markdown("[🚌 Bus Timetable](https://www.comazzibus.com/)")
st.sidebar.markdown("[🚆 Trenitalia](https://www.trenitalia.com/)")
st.sidebar.markdown("[🚆 SBB](https://www.sbb.ch/)")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Activities")

st.sidebar.markdown("""
- 🏔️ Zermatt Hikes  
[Explore](https://www.earthtrekkers.com/best-hikes-in-zermatt/)
- 🏔️ Brig Activities  
[Explore](https://www.myswitzerland.com/en/destinations/eggishorn-viewpoint-look-out-over-the-great-aletsch-glacier/)
""")

# =========================
# 📑 TABS
# =========================
tab1, tab2 = st.tabs(["🏔️ Daily Plan", "🚆 Transport Info"])

# =========================
# 🏔️ TAB 1 — DAILY PLAN
# =========================
with tab1:

    row = df[df["day"] == day].iloc[0]

    st.title(f"Day {row['day']}: {row['from']} → {row['to']}")
    st.caption(row["date"])

    st.markdown(f"[🗺️ Open Full Route (Wikiloc)]({wikiloc_url})")

    # --- Metrics ---
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Distance",
        f"{row['distance_km']} km" if pd.notna(row['distance_km']) else "-"
    )

    col2.metric(
        "Elevation ↑",
        f"{row['elevation_up']} m" if pd.notna(row['elevation_up']) else "-"
    )

    col3.metric(
        "Time",
        f"{row['time_h']} h" if pd.notna(row['time_h']) else "-"
    )

    

    # --- Accommodation ---
    st.subheader("🏠 Accommodation")

    st.write(f"**{row['stay']}**")
    st.write(f"💰 Cost: {row['cost']} {row['currency']}")

    if row.get("link"):
        st.markdown(f"[🔗 Open booking / website]({row['link']})")
        st.caption("👉 Opens in browser")

    # --- Notes ---
    if row["notes"]:
        st.subheader("⚠️ Notes")
        st.markdown(row["notes"])

    # =========================
    # 📊 SUMMARY
    # =========================
    st.markdown("---")
    st.subheader("📊 Trip Summary")

    col1, col2, col3 = st.columns(3)

    total_km = df["distance_km"].sum(skipna=True)
    total_up = df["elevation_up"].sum(skipna=True)
    total_cost = df["cost"].sum()

    col1.metric("Total Distance", f"{round(total_km,1)} km")
    col2.metric("Total Elevation ↑", f"{int(total_up)} m")
    st.metric("Total Cost per person (EUR)", f"{int(total_eur/6)} €")

    # =========================
    # 📈 ELEVATION CHART
    # =========================
    st.subheader("📈 Elevation Gain & Loss per Day")

    df["elevation_down_neg"] = -df["elevation_down"].fillna(0)

    chart_df = df.melt(
        id_vars="day",
        value_vars=["elevation_up", "elevation_down_neg"],
        var_name="type",
        value_name="meters"
    )

    chart_df["type"] = chart_df["type"].replace({
        "elevation_up": "Elevation Up",
        "elevation_down_neg": "Elevation Down"
    })

    chart = alt.Chart(chart_df).mark_bar().encode(
        x=alt.X("day:O", title="Day"),
        y=alt.Y("meters:Q", title="Meters"),
        color=alt.Color("type:N", legend=alt.Legend(title="Type")),
        tooltip=["day", "type", "meters"]
    )

    st.altair_chart(chart, use_container_width=True)

    # =========================
    # 🗺️ ROUTE MAP (GPX)
    # =========================
    st.markdown("---")
    st.subheader("🗺️ Route Map")

    # Load GPX
    with open("tmr.gpx", "r") as f:
        gpx = gpxpy.parse(f)

    # Extract points
    points = [
        (p.latitude, p.longitude)
        for track in gpx.tracks
        for segment in track.segments
        for p in segment.points
    ]

    # Create map
    m = folium.Map(location=points[0], zoom_start=10)

    # Draw route
    folium.PolyLine(points, color="blue", weight=4).add_to(m)
    folium.Marker(points[0], tooltip="Start").add_to(m)
    folium.Marker(points[-1], tooltip="End").add_to(m)
    # Show map in Streamlit
    st.components.v1.html(m._repr_html_(), height=500)

# =========================
# 🚆 TAB 2 — TRANSPORT
# =========================
with tab2:

    st.title("🚆 Transport & Logistics")

    # --- Flights ---
    with st.expander("✈️ Flights"):
        st.markdown("""
        **Athens → Milan**  
        (add flight details)

        **Return: Milan → Athens**  
        (add return flight)
        """)

    # --- Train Italy ---
    with st.expander("🚆 Train: Milano → Domodossola"):
        st.markdown("""
        - Departure: Milano Centrale  
        - Duration: ~1h30  

        👉 [Check Trenitalia](https://www.trenitalia.com/)
        """)

    # --- Bus ---
    with st.expander("🚌 Bus: Domodossola → Macugnaga"):
        st.markdown("""
        - Last departure: 17:30  

        👉 [Bus timetable](https://www.comazzibus.com/)
        """)

    # --- Switzerland ---
    with st.expander("🚆 Swiss Transport (Zermatt / Brig)"):
        st.markdown("""
        - Zermatt → Brig (train)  
        - Brig → Milan (train)  

        👉 [SBB Timetable](https://www.sbb.ch/)
        """)

    # --- Notes ---
    st.markdown("---")
    st.subheader("🧠 Useful Tips")

    st.markdown("""
    - Arrive early for connections  
    - Swiss trains are very punctual  
    - Check last bus times carefully  
    - Save tickets offline  
    """)