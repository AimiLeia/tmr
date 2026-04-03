import streamlit as st
import pandas as pd
import altair as alt
import folium
import gpxpy
import base64
from data import load_data

# =========================
# ⚙️ CONFIG
# =========================
st.set_page_config(
    page_title="Monte Rosa Tour",
    page_icon="🏔️",
    layout="wide"
)

CHF_TO_EUR = 1.04

# =========================
# 📦 LOAD DATA
# =========================
df = load_data()

def convert_to_eur(row):
    if row["currency"] == "CHF":
        return row["cost"] * CHF_TO_EUR
    return row["cost"]

df["cost_eur"] = df.apply(convert_to_eur, axis=1)
total_eur = df["cost_eur"].sum()

# =========================
# 🖼️ HERO IMAGE
# =========================
def get_base64(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

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
# 🧭 DAY NAVIGATION (MOBILE FRIENDLY)
# =========================
if "day" not in st.session_state:
    st.session_state.day = 1

col1, col2, col3 = st.columns([1,2,1])

if col1.button("⬅️", use_container_width=True):
    st.session_state.day = max(1, st.session_state.day - 1)

col2.markdown(f"### Day {st.session_state.day}")

if col3.button("➡️", use_container_width=True):
    st.session_state.day = min(df["day"].max(), st.session_state.day + 1)

day = st.session_state.day
row = df[df["day"] == day].iloc[0]

# =========================
# 🔀 VIEW SELECTOR
# =========================
view = st.radio(
    "View",
    ["🏔️ Plan", "🚆 Transport"],
    horizontal=True
)

# =========================
# 🏔️ DAILY PLAN
# =========================
if view == "🏔️ Plan":

    st.title(f"{row['from']} → {row['to']}")
    st.caption(row["date"])

    # Quick cost info
    st.info(f"💰 ~{int(total_eur/6)}€ per person")

    # --- Metrics (mobile optimized) ---
    col1, col2 = st.columns(2)

    col1.metric(
        "Distance",
        f"{row['distance_km']} km" if pd.notna(row['distance_km']) else "-"
    )

    col2.metric(
        "Elevation ↑",
        f"{row['elevation_up']} m" if pd.notna(row['elevation_up']) else "-"
    )

    st.metric(
        "Time",
        f"{row['time_h']} h" if pd.notna(row['time_h']) else "-"
    )

    st.markdown("---")

    # --- Accommodation ---
    st.subheader("🏠 Accommodation")

    st.write(f"**{row['stay']}**")
    st.write(f"💰 {row['cost']} {row['currency']}")

    if row.get("link"):
        st.markdown(f"[🔗 Open booking]({row['link']})")

    # --- Notes ---
    if row["notes"]:
        st.subheader("⚠️ Notes")
        st.markdown(row["notes"])

    st.markdown("---")

    # =========================
    # 📈 ELEVATION CHART
    # =========================
    st.subheader("📈 Elevation")

    df["elevation_down_neg"] = -df["elevation_down"].fillna(0)

    chart_df = df.melt(
        id_vars="day",
        value_vars=["elevation_up", "elevation_down_neg"],
        var_name="type",
        value_name="meters"
    )

    chart_df["type"] = chart_df["type"].replace({
        "elevation_up": "Up",
        "elevation_down_neg": "Down"
    })

    chart = alt.Chart(chart_df).mark_bar().encode(
        x=alt.X("day:O"),
        y=alt.Y("meters:Q"),
        color="type:N"
    )

    st.altair_chart(chart, use_container_width=True)

    st.markdown("---")

    # =========================
    # 🗺️ MAP
    # =========================
    st.subheader("🗺️ Route")

    try:
        with open("tmr.gpx", "r") as f:
            gpx = gpxpy.parse(f)

        points = [
            (p.latitude, p.longitude)
            for track in gpx.tracks
            for segment in track.segments
            for p in segment.points
        ]

        m = folium.Map(location=points[0], zoom_start=10)
        folium.PolyLine(points, weight=4).add_to(m)

        folium.Marker(points[0], tooltip="Start").add_to(m)
        folium.Marker(points[-1], tooltip="End").add_to(m)

        st.components.v1.html(m._repr_html_(), height=400)

    except:
        st.warning("Map not available")

# =========================
# 🚆 TRANSPORT
# =========================
else:

    st.title("🚆 Transport")

    with st.expander("✈️ Flights"):
        st.markdown("""
        Athens → Milan  
        Milan → Athens
        """)

    with st.expander("🚆 Train"):
        st.markdown("""
        Milano → Domodossola  
        👉 https://www.trenitalia.com/
        """)

    with st.expander("🚌 Bus"):
        st.markdown("""
        Domodossola → Macugnaga  
        👉 https://www.comazzibus.com/
        """)

    with st.expander("🚆 Switzerland"):
        st.markdown("""
        Zermatt → Brig → Milan  
        👉 https://www.sbb.ch/
        """)