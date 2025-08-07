# 📊 Dead Hour Optimizer – Streamlit

import streamlit as st
import sys
import os
import pandas as pd
import requests
import plotly.express as px
from datetime import date

# 👇 Zet dit vóór de import!
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

# ✅ Nu pas importeren
from shop_mapping import SHOP_NAME_MAP
from data_transformer import normalize_vemcount_response

# -----------------------------
# CONFIGURATIE
# -----------------------------
API_URL = st.secrets["API_URL"].rstrip("/")
DEFAULT_SHOP_IDS = list(SHOP_NAME_MAP.keys())

# -----------------------------
# API CLIENT
# -----------------------------
def get_kpi_data_for_store(shop_id, period="last_8_weeks", step="hour"):
    params = [("data", shop_id)]
    params += [
        ("data_output", "count_in"),
        ("data_output", "conversion_rate"),
        ("data_output", "turnover"),
        ("data_output", "sales_per_visitor"),
        ("source", "shops"),
        ("period", period),
        ("step", step)
    ]
    try:
        response = requests.post(API_URL, params=params)
        if response.status_code == 200:
            full_response = response.json()
            if "data" in full_response and period in full_response["data"]:
                raw_data = full_response["data"][period]
                return normalize_vemcount_response(raw_data)
        else:
            st.error(f"❌ Error fetching data: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"🚨 API call exception: {e}")
    return pd.DataFrame()

# -----------------------------
# SIMULATIE
# -----------------------------
def find_deadhours_and_simulate(df: pd.DataFrame) -> pd.DataFrame:
    df["weekday"] = pd.to_datetime(df["timestamp"]).dt.day_name()
    df["hour"] = pd.to_datetime(df["timestamp"]).dt.strftime("%H:00")

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

    return df_grouped.sort_values("extra_turnover", ascending=False)

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Dead Hour Optimizer", layout="wide")
st.title("🧠 Dead Hour Optimizer")
st.markdown("Simuleer omzetgroei door structureel zwakke uren te verbeteren op basis van sales per visitor.")

ID_TO_NAME = SHOP_NAME_MAP
NAME_TO_ID = {v: k for k, v in SHOP_NAME_MAP.items()}

selected_name = st.selectbox("Selecteer een winkel", options=list(NAME_TO_ID.keys()), index=0)
shop_id = NAME_TO_ID[selected_name]

period = st.selectbox("Kies analyseperiode", options=["last_4_weeks", "last_8_weeks", "last_12_weeks"], index=1)

if st.button("🔍 Analyseer Dead Hours"):
    with st.spinner("Data ophalen en analyseren..."):
        df_kpi = get_kpi_data_for_store(shop_id, period=period)

    if not df_kpi.empty:
        df_results = find_deadhours_and_simulate(df_kpi)

        st.subheader(f"📊 Dead hours voor {selected_name}")
        display_df = df_results[["weekday", "hour", "count_in", "conversion_rate", "sales_per_visitor", "original", "uplift", "extra_turnover"]].copy()
        display_df.columns = ["Weekdag", "Uur", "Bezoekers", "Conversie (%)", "SPV", "Originele omzet", "Nieuwe omzet", "Extra omzet"]

        st.dataframe(display_df.style.format({
            "Conversie (%)": "{:.1f}",
            "SPV": "€{:,.2f}",
            "Originele omzet": "€{:,.0f}",
            "Nieuwe omzet": "€{:,.0f}",
            "Extra omzet": "€{:,.0f}"
        }), use_container_width=True)

        st.markdown("### 📈 Grootste omzetpotentie per uur")
        fig = px.bar(
            df_results,
            x="extra_turnover",
            y="weekday",
            color="hour",
            orientation="h",
            labels={"extra_turnover": "Extra omzet (€)", "weekday": "Weekdag", "hour": "Uur"},
            title="Dead Hours met hoogste omzetpotentie"
        )
        fig.update_layout(xaxis_tickprefix="€", yaxis_title="Weekdag")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Geen data beschikbaar voor deze periode.")
