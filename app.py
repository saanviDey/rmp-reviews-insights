import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Load Data ---
df = pd.read_csv("professor_profiles.csv")

# --- Page Config ---
st.set_page_config(page_title="Professor Insight", layout="centered")
st.title("🎓 Professor Insight")
st.caption("A deeper look at what students really think")

professor_list = sorted(df["professor"].dropna().unique().tolist())
selected_name = st.selectbox("Select a professor", ["-- Select --"] + professor_list)

if selected_name != "-- Select --":
    prof = df[df["professor"] == selected_name].iloc[0]

    # --- Professor Header ---
    st.subheader(f"📋 {prof['professor']}")
    
    col1, col2 = st.columns(2)
    col1.metric("Avg Rating", f"{prof['avgRating']:.1f} / 5")
    col2.metric("Total Reviews", int(prof["numRatings"]))

    # --- Aspect Breakdown Chart ---
    aspects = [
        "harsh grading",
        "great teaching",
        "poor teaching",
        "engaging lectures",
        "boring lectures",
        "heavy workload",
        "approachable and kind",
        "unavailable or unhelpful"
    ]

    available = [a for a in aspects if a in prof.index]
    scores = [prof[a] for a in available]

    positive = {"great teaching", "engaging lectures", "approachable and kind"}
    colors = ["#4CAF50" if a in positive else "#F44336" for a in available]

    fig = go.Figure(go.Bar(
        x=scores,
        y=available,
        orientation="h",
        marker_color=colors,
        text=[f"{s:.0%}" for s in scores],
        textposition="outside"
    ))

    fig.update_layout(
        title="Aspect Breakdown",
        xaxis=dict(range=[0, 1], tickformat=".0%"),
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Raw Reviews ---
    st.subheader("💬 Sample Reviews")
    reviews_df = pd.read_csv("rmp_reviews_scored.csv")
    prof_reviews = reviews_df[reviews_df["professor"] == prof["professor"]]["comment"].head(5)
    
    for review in prof_reviews:
        st.markdown(f"> {review}")
        st.divider()


df = pd.read_csv("professor_profiles.csv")
print(df.columns.tolist())
print(df.head(2))