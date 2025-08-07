import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    for shop_id, shop_content in response_json.items():
        dates = shop_content.get("dates", {})
        for date_label, day_info in dates.items():
            data = day_info.get("data", {})

            row = {
                "shop_id": int(shop_id),
                "date": data.get("dt"),
                "turnover": float(data.get("turnover", 0)),
                "count_in": float(data.get("count_in", 0)),
                "conversion_rate": float(data.get("conversion_rate", 0)),
                "sales_per_transaction": float(data.get("sales_per_transaction") or 0),
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

    return df

def normalize_hourly_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    # Loop over shop_ids en datumgroepen
    for day_key, shop_data in response_json.get("data", {}).items():
        for shop_id, shop_content in shop_data.items():
            dates = shop_content.get("dates", {})
            for hour_label, hour_data in dates.items():
                data = hour_data.get("data", {})

                row = {
                    "shop_id": int(shop_id),
                    "timestamp": pd.to_datetime(data.get("dt")),
                    "sales_per_visitor": float(data.get("sales_per_visitor") or 0),
                    "turnover": float(data.get("turnover", 0) or 0),
                    "count_in": float(data.get("count_in", 0) or 0),
                    "conversion_rate": float(data.get("conversion_rate", 0) or 0)
                }
                rows.append(row)

    df = pd.DataFrame(rows)
    return df
