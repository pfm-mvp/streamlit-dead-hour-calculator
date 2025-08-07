import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    # Detecteer of 'data' key aanwezig is → dit duidt op het nieuwe geneste formaat
    root_data = response_json.get("data", response_json)

    for date_key, locations in root_data.items():
        for shop_id, content in locations.items():
            dates = content.get("dates", {})
            for label, hour_data in dates.items():
                d = hour_data.get("data", {})
                if not d:
                    continue
                rows.append({
                    "shop_id": int(shop_id),
                    "timestamp": pd.to_datetime(d.get("dt")),
                    "count_in": float(d.get("count_in", 0)),
                    "conversion_rate": float(d.get("conversion_rate", 0)),
                    "turnover": float(d.get("turnover", 0)),
                    "sales_per_visitor": float(d.get("sales_per_visitor", 0))
                })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df
