import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    # ✅ Nieuw responsformaat detecteren (datumlabels aan buitenkant)
    if "data" in response_json and any(k.startswith("date_") for k in response_json["data"]):
        for date_key, shops in response_json["data"].items():
            for shop_id, shop_content in shops.items():
                dates = shop_content.get("dates", {})
                for hour_key, hour_data in dates.items():
                    data = hour_data.get("data", {})
                    rows.append({
                        "shop_id": int(shop_id),
                        "timestamp": pd.to_datetime(data.get("dt")),
                        "turnover": float(data.get("turnover") or 0),
                        "count_in": float(data.get("count_in") or 0),
                        "conversion_rate": float(data.get("conversion_rate") or 0),
                        "sales_per_visitor": float(data.get("sales_per_visitor") or 0),
                    })

    # ✅ Oud responsformaat
    else:
        for shop_id, shop_content in response_json.items():
            dates = shop_content.get("dates", {})
            for date_label, day_info in dates.items():
                data = day_info.get("data", {})

                rows.append({
                    "shop_id": int(shop_id),
                    "date": pd.to_datetime(data.get("dt")),
                    "turnover": float(data.get("turnover", 0)),
                    "count_in": float(data.get("count_in", 0)),
                    "conversion_rate": float(data.get("conversion_rate", 0)),
                    "sales_per_transaction": float(data.get("sales_per_transaction") or 0),
                })

    df = pd.DataFrame(rows)

    if not df.empty:
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        elif "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

    return df
