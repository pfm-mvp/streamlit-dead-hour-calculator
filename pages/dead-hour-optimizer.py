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

# -----------------------------
# CONFIGURATIE
# -----------------------------
API_URL = st.secrets["API_URL"].rstrip("/")
DEFAULT_SHOP_IDS = list(SHOP_NAME_MAP.keys())

# -----------------------------
# API CLIENT
# -----------------------------
def get_hourly_kpis(shop_id: int, date_str: str) -> pd.DataFrame:
    params = [
        ("data", shop_id),
        ("source", "shops"),
        ("period", "date"),
        ("date", date_str),
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
            df["hour"] = pd.to_datetime(df["timestamp"]).dt.strftime("%H:00")
            df = df.groupby("hour")[[
                "count_in", "conversion_rate", "turnover", "inside", "sales_per_visitor"
            ]].sum().reset_index()
            return df
        else:
            st.error(f"❌ Error fetching data: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"🚨 API call exception: {e}")
    return pd.DataFrame()

# -----------------------------
# SIMULATIE
# -----------------------------
def simulate_hourly_uplift(df: pd.DataFrame) -> pd.DataFrame:
    avg_spv = df["sales_per_visitor"].mean()
    df["original"] = df["turnover"]
    df["uplift"] = df.apply(
        lambda row: row["count_in"] * avg_spv if row["sales_per_visitor"] < avg_spv else row["turnover"], axis=1)
    df["extra_turnover"] = df["uplift"] - df["turnover"]
    df["growth_pct"] = (df["extra_turnover"] / df["turnover"]).replace([float('inf'), -float('inf')], 0)
    return df

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Dead Hour Optimizer", layout="wide")
st.title("🧠 Dead Hour Optimizer")
st.markdown("Simuleer omzetgroei door de zwakste uren te verbeteren.")

ID_TO_NAME = SHOP_NAME_MAP
NAME_TO_ID = {v: k for k, v in SHOP_NAME_MAP.items()}

default_names = [ID_TO_NAME.get(shop_id, str(shop_id)) for shop_id in DEFAULT_SHOP_IDS]
selected_names = st.selectbox("Selecteer een winkel", options=list(NAME_TO_ID.keys()), index=0)
shop_id = NAME_TO_ID[selected_names]

selected_date = st.date_input("Selecteer een datum", value=date.today())

# ✅ Data ophalen
df = get_hourly_kpis(shop_id, selected_date.strftime("%Y-%m-%d"))

if not df.empty:
    df_result = simulate_hourly_uplift(df)

    st.subheader(f"📊 Analyse voor {selected_names} op {selected_date.strftime('%A %d %B %Y')}")
    worst_hour = df_result.sort_values("sales_per_visitor").iloc[0]

    st.markdown(f"### ❌ Slechtst presterend uur: **{worst_hour['hour']}**")
    st.metric("Bezoekers", int(worst_hour["count_in"]))
    st.metric("Conversie", f"{worst_hour['conversion_rate']:.1f}%")
    st.metric("Bezoekerswaarde", f"€{worst_hour['sales_per_visitor']:,.2f}")

    st.markdown("---")
    st.markdown("### 💸 Simulatie omzetgroei per uur")

    display_df = df_result[["hour", "count_in", "conversion_rate", "sales_per_visitor", "original", "uplift", "extra_turnover"]]
    display_df.columns = ["Uur", "Bezoekers", "Conversie (%)", "Bezoekerswaarde (SPV)", "Originele omzet", "Nieuwe omzet", "Extra omzet"]

    st.dataframe(display_df.style.format({
        "Conversie (%)": "{:.1f}",
        "Bezoekerswaarde (SPV)": "€{:,.2f}",
        "Originele omzet": "€{:,.0f}",
        "Nieuwe omzet": "€{:,.0f}",
        "Extra omzet": "€{:,.0f}"
    }), use_container_width=True)

    fig = px.bar(
        df_result,
        x="hour",
        y="extra_turnover",
        labels={"hour": "Uur", "extra_turnover": "Extra omzet (€)"},
        title="Uren met het grootste omzetpotentieel",
        text_auto='.2s'
    )
    fig.update_layout(yaxis_tickprefix="€", xaxis_title="Uur van de dag")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Geen data gevonden voor deze combinatie van winkel en datum.")
