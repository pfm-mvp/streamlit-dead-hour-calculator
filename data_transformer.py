import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    for shop_id, shop_content in response_json.items():
        if not isinstance(shop_content, dict):
            continue

        dates_container = shop_content.get("dates", {})

        for date_key, date_info in dates_container.items():
            if not isinstance(date_info, dict):
                continue

            data = date_info.get("data", {})

            row = {
                "shop_id": int(shop_id),
                "timestamp": data.get("dt"),
                "turnover": float(data.get("turnover", 0) or 0),
                "count_in": float(data.get("count_in", 0) or 0),
                "conversion_rate": float(data.get("conversion_rate", 0) or 0),
                "sales_per_transaction": float(data.get("sales_per_transaction") or 0),
                "sales_per_visitor": float(data.get("sales_per_visitor") or 0),
            }
            rows.append(row)

    df = pd.DataFrame(rows)

    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df
