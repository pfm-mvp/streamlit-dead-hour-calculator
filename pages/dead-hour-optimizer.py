# 📊 Dead Hour Optimizer – Streamlit

import streamlit as st
import sys
import os
import pandas as pd
import requests
import plotly.express as px
from datetime import date, timedelta

# 👇 Set up imports
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

# ✅ Load shared data
from shop_mapping import SHOP_NAME_MAP

# -----------------------------
# CONFIGURATION
# -----------------------------
API_URL = st.secrets["API_URL"].rstrip("/")
DEFAULT_SHOP_IDS = list(SHOP_NAME_MAP.keys())

# -----------------------------
# API CLIENT
# -----------------------------
def get_kpi_data(shop_id: int, start_date: str, end_date: str) -> pd.DataFrame:
    params = [
        ("data", shop_id),
        ("source", "shops"),
        ("period", "date"),
        ("from", start_date),
        ("to", end_date),
        ("interval", "hour"),
        ("data_output", "count_in"),
        ("data_output", "conversion_rate"),
        ("data_output", "turnover"),
        ("data_output", "inside"),
        ("data_output", "sales_per_visitor")
    ]
    try:
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["weekday"] = df["timestamp"].dt.day_name()
            df["hour"] = df["timestamp"].dt.strftime("%H:00")
            return df
        else:
            st.error(f"❌ Error fetching data: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"🚨 API call exception: {e}")
    return pd.DataFrame()

# -----------------------------
# SIMULATION
# -----------------------------
def find_deadhours_and_simulate(df: pd.DataFrame) -> pd.DataFrame:
    df_grouped = df.groupby(["weekday", "hour"]).agg({
        "count_in": "sum",
        "conversion_rate": "mean",
        "turnover": "sum",
        "sales_per_visitor": "mean"
    }).reset_index()

    avg_spv = df_grouped["sales_per_visitor"].mean()
    df_grouped["original"] = df_grouped["turnover"]
    df_grouped["uplift"] = df_grouped.apply(
        lambda row: row["count_in"] * avg_spv if row["sales_per_visitor"] < avg_spv else row["turnover"], axis=1)
    df_grouped["extra_turnover"] = df_grouped["uplift"] - df_grouped["turnover"]
    df_grouped["growth_pct"] = (df_grouped["extra_turnover"] / df_grouped["turnover"]).replace([float('inf'), -float('inf')], 0)

    result = df_grouped.sort_values("extra_turnover", ascending=False)
    return result

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Dead Hour Optimizer", layout="wide")
st.title("🧠 Dead Hour Optimizer")
st.markdown("Simulate potential revenue uplift by identifying consistently weak hours per weekday.")

ID_TO_NAME = SHOP_NAME_MAP
NAME_TO_ID = {v: k for k, v in SHOP_NAME_MAP.items()}

default_names = [ID_TO_NAME.get(shop_id, str(shop_id)) for shop_id in DEFAULT_SHOP_IDS]
selected_name = st.selectbox("Select a store", options=list(NAME_TO_ID.keys()), index=0)
shop_id = NAME_TO_ID[selected_name]

weeks = st.slider("Select analysis period (in weeks)", min_value=2, max_value=12, value=4)
end_date = date.today()
start_date = end_date - timedelta(weeks=weeks)

st.markdown(f"🗓️ Analysis period: **{start_date.strftime('%Y-%m-%d')}** to **{end_date.strftime('%Y-%m-%d')}**")

limit_top_3 = st.checkbox("Show only top 3 dead hours per weekday", value=False)

if st.button("🔍 Analyze dead hours"):
    with st.spinner("Fetching data and identifying opportunities..."):
        df_kpi = get_kpi_data(shop_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

    if not df_kpi.empty:
        df_results = find_deadhours_and_simulate(df_kpi)

        if limit_top_3:
            df_results = df_results.sort_values("extra_turnover", ascending=False)
            df_results = df_results.groupby("weekday").head(3).reset_index(drop=True)

        st.subheader(f"📊 Dead hours for {selected_name}")
        display_df = df_results[["weekday", "hour", "count_in", "conversion_rate", "sales_per_visitor", "original", "uplift", "extra_turnover"]].copy()
        display_df.columns = ["Weekday", "Hour", "Visitors", "Conversion (%)", "Sales per Visitor (SPV)", "Original Turnover", "Optimized Turnover", "Extra Turnover"]

        st.dataframe(display_df.style.format({
            "Conversion (%)": "{:.1f}",
            "Sales per Visitor (SPV)": "€{:,.2f}",
            "Original Turnover": "€{:,.0f}",
            "Optimized Turnover": "€{:,.0f}",
            "Extra Turnover": "€{:,.0f}"
        }), use_container_width=True)

        st.markdown("### 📈 Highest Potential Dead Hours")
        fig = px.bar(
            df_results,
            x="extra_turnover",
            y="weekday",
            color="hour",
            orientation="h",
            labels={"extra_turnover": "Extra Turnover (€)", "weekday": "Weekday", "hour": "Hour"},
            title="Dead Hours with Highest Potential"
        )
        fig.update_layout(xaxis_tickprefix="€", yaxis_title="Weekday")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("⚠️ No data found for this period.")
