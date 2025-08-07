# 📊 Dead Hour Optimizer – Streamlit

import streamlit as st
import sys
import os
import pandas as pd
import requests
import plotly.express as px
from datetime import date, timedelta
from urllib.parse import urlencode
import numpy as np

st.cache_data.clear()
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from shop_mapping import SHOP_NAME_MAP
from data_transformer import normalize_vemcount_response

API_URL = st.secrets["API_URL"].rstrip("/")
DEFAULT_SHOP_IDS = list(SHOP_NAME_MAP.keys())

def get_kpi_data_for_store(shop_id, start_date, end_date, start_hour, end_hour) -> pd.DataFrame:
    start_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    end_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")

    params = [
        ("data", shop_id),
        ("data_output", "count_in"),
        ("data_output", "conversion_rate"),
        ("data_output", "turnover"),
        ("data_output", "sales_per_visitor"),
        ("data_output", "sales_per_transaction"),
        ("source", "shops"),
        ("period", "date"),
        ("form_date_from", start_date),
        ("form_date_to", end_date),
        ("step", "hour"),
        ("show_hours_from", f"{start_hour:02d}:00"),
        ("show_hours_to", f"{end_hour:02d}:00")
    ]

    query_string = urlencode(params, doseq=True).replace('%3A', ':')
    url = f"{API_URL}?{query_string}"

    try:
        response = requests.post(url)
        if response.status_code == 200:
            raw_data = response.json()
            if "data" in raw_data and raw_data["data"]:
                df = normalize_vemcount_response(raw_data)
                df["hour"] = pd.to_datetime(df["datetime"]).dt.hour
                df = df[(df["hour"] >= start_hour) & (df["hour"] < end_hour)]
                return df
            else:
                st.warning("⚠️ De API gaf een lege dataset terug.")
        else:
            st.error(f"❌ Error fetching data: {response.status_code}")
    except Exception as e:
        st.error(f"🚨 API call exception: {e}")

    return pd.DataFrame()

def find_deadhours_and_simulate(df: pd.DataFrame) -> pd.DataFrame:
    df["weekday"] = pd.to_datetime(df["datetime"]).dt.day_name()
    df["hour"] = pd.to_datetime(df["datetime"]).dt.strftime("%H:00")
    df["datetime"] = pd.to_datetime(df["datetime"])

    df_grouped = df.groupby(["weekday", "hour"]).agg({
        "count_in": "sum",
        "conversion_rate": "mean",
        "turnover": "sum",
        "sales_per_visitor": "mean",
        "sales_per_transaction": "mean"
    }).reset_index()

    avg_spv = df_grouped["sales_per_visitor"].mean()
    df_grouped["original"] = df_grouped["turnover"]
    df_grouped["uplift"] = df_grouped.apply(
        lambda row: row["count_in"] * avg_spv if row["sales_per_visitor"] < avg_spv else row["turnover"], axis=1)
    df_grouped["extra_turnover"] = df_grouped["uplift"] - df_grouped["turnover"]

    return df_grouped.sort_values("extra_turnover", ascending=False)

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Dead Hour Optimizer", layout="wide")
st.title("🧐 Dead Hour Optimizer")
st.markdown("Simuleer omzetgroei door structureel zwakke uren te verbeteren op basis van sales per visitor.")

ID_TO_NAME = SHOP_NAME_MAP
NAME_TO_ID = {v: k for k, v in SHOP_NAME_MAP.items()}

selected_name = st.selectbox("Selecteer een winkel", options=list(NAME_TO_ID.keys()), index=0)
shop_id = NAME_TO_ID[selected_name]

days = st.slider("Analyseer over hoeveel dagen terug?", min_value=7, max_value=90, step=7, value=30)
end_date = date.today()
start_date = end_date - timedelta(days=days)

opening_hours = st.slider(
    "⏰ Selecteer openingstijden",
    min_value=0,
    max_value=24,
    value=(9, 19),
    step=1,
    format="%02d:00"
)

min_visitors = st.slider("Minimaal gemiddeld aantal bezoekers per uur (filter)", min_value=0, max_value=20, value=2, step=1)

filter_transactions = st.checkbox("Toon alleen uren met transacties")

toggle = st.radio(
    "🔁 Toon omzetpotentie op basis van:",
    ["Resterend jaar", "Volledig jaar (52 weken)"],
    horizontal=True
)

st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #F04438;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

btn = st.button("Analyseer Dead Hours", type="primary")
if btn:
    start_hour, end_hour = opening_hours
    with st.spinner("Data ophalen en analyseren..."):
        df_kpi = get_kpi_data_for_store(shop_id, start_date, end_date, start_hour, end_hour)

    if not df_kpi.empty:
        df_results = find_deadhours_and_simulate(df_kpi)

        st.markdown("### 🔥 Dead Hours per Weekdag (gemiddelde omzetpotentie)")

        best_deadhours = (
            df_results[df_results["extra_turnover"] > 0]
            .groupby(["weekday", "hour"])["extra_turnover"]
            .mean()
            .reset_index()
            .sort_values("extra_turnover", ascending=False)
            .groupby("weekday")
            .head(1)
            .reset_index(drop=True)
        )

        vandaag = date.today()
        jaar_einde = date(vandaag.year, 12, 31)
        weken_over = 52 if toggle == "Volledig jaar (52 weken)" else ((jaar_einde - vandaag).days) // 7

        best_deadhours["Jaarpotentie (52w)"] = best_deadhours["extra_turnover"] * 52
        best_deadhours["Jaarpotentie (realistisch)"] = best_deadhours["extra_turnover"] * weken_over

        df_kpi["weekday"] = pd.to_datetime(df_kpi["datetime"]).dt.day_name()
        df_kpi["hour"] = pd.to_datetime(df_kpi["datetime"]).dt.strftime("%H:00")

        kpi_lookup = df_kpi.groupby(["weekday", "hour"]).agg({
            "count_in": "mean",
            "conversion_rate": "mean",
            "sales_per_transaction": "mean"
        }).reset_index().rename(columns={
            "count_in": "Bezoekers",
            "conversion_rate": "Conversie (%)",
            "sales_per_transaction": "ATV (€)"
        })

        best_deadhours = best_deadhours.merge(kpi_lookup, on=["weekday", "hour"], how="left")
        best_deadhours[["Bezoekers", "Conversie (%)", "ATV (€)"]] = best_deadhours[["Bezoekers", "Conversie (%)", "ATV (€)"]].fillna(0)

        best_deadhours = best_deadhours[best_deadhours["Bezoekers"] >= min_visitors]
        if filter_transactions:
            best_deadhours = best_deadhours[best_deadhours["ATV (€)"] > 0]

        best_deadhours["Conversie (%)"] = best_deadhours["Conversie (%)"].apply(lambda x: x*100 if x < 1 else x)

        top_5 = best_deadhours.nlargest(5, "extra_turnover")
        week_sum = top_5["extra_turnover"].sum()
        year_sum = week_sum * weken_over

        st.markdown(
            f"💡 **Top 5 momenten** = €{week_sum:,.0f} / week ≈ **€{year_sum:,.0f} extra omzet/jaar**"
        )

        ordered_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        best_deadhours["weekday"] = pd.Categorical(best_deadhours["weekday"], categories=ordered_days, ordered=True)
        best_deadhours = best_deadhours.sort_values("weekday")

        with st.expander("📊 Uitleg kolommen"):
            st.markdown("""
            - **Bezoekers** = Gemiddeld aantal bezoekers per week op dat uur
            - **Conversie (%)** = Gemiddeld conversiepercentage (aantal transacties / aantal bezoekers)
            - **ATV (€)** = Gemiddeld bonbedrag per transactie op dat uur
            """)

        st.dataframe(best_deadhours[[
            "weekday", "hour", "extra_turnover",
            "Jaarpotentie (52w)", "Jaarpotentie (realistisch)",
            "Bezoekers", "Conversie (%)", "ATV (€)"
        ]].rename(columns={
            "weekday": "Weekdag",
            "hour": "Uur",
            "extra_turnover": "Extra omzet (per week)",
        }).style.format({
            "Extra omzet (per week)": "€{:,.0f}",
            "Jaarpotentie (52w)": "€{:,.0f}",
            "Jaarpotentie (realistisch)": "€{:,.0f}",
            "Bezoekers": "{:,.0f}",
            "Conversie (%)": "{:.1f}%",
            "ATV (€)": "€{:,.0f}"
        }), use_container_width=True)

        st.caption("💡 *SPV = Conversie × Bonbedrag (ATV)* — deze tabel laat zien hoeveel extra omzet te winnen is per uur per weekdag.")

        fig2 = px.bar(
            best_deadhours.sort_values("weekday"),
            x="extra_turnover",
            y="weekday",
            color="hour",
            orientation="h",
            labels={"extra_turnover": "Extra omzet (€)", "weekday": "Weekdag", "hour": "Uur"},
            title="Dead Hours met hoogste omzetpotentie per weekdag",
            color_discrete_sequence=px.colors.sequential.Viridis,
            category_orders={"weekday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
        )
        fig2.update_layout(
    xaxis_tickprefix="€",
    yaxis_title="Weekdag",
    legend_title="Uur",
    hoverlabel=dict(
        namelength=-1,
        bgcolor="white",
        font_size=14,
        font_family="Arial"
    ),
    hovermode="closest",
    xaxis_tickformat=",.2f"
)
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning("⚠️ Geen data beschikbaar voor deze periode.")
