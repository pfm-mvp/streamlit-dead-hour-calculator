import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    data_block = response_json.get("data", {})
    for date_key, shops in data_block.items():
        for shop_id, content in shops.items():
            dates = content.get("dates", {})
            for timestamp, hour_info in dates.items():
                metrics = hour_info.get("data", {})
                row = {
                    "shop_id": int(shop_id),
                    "timestamp": metrics.get("dt"),
                    "count_in": float(metrics.get("count_in", 0)),
                    "conversion_rate": float(metrics.get("conversion_rate", 0)),
                    "turnover": float(metrics.get("turnover", 0)),
                    "sales_per_visitor": float(metrics.get("sales_per_visitor", 0)),
                }
                rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df
