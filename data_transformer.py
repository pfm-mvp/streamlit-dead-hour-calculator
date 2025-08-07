import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    # ✅ Stap 1: response bevat altijd 1 key: "data"
    all_data = response_json.get("data", {})

    for date_block_key, date_block in all_data.items():  # bijv. 'date_2025-08-01'
        for shop_id, shop_content in date_block.items():
            shop_id = int(shop_id)

            # ✅ Nu per timestamp entry
            for timestamp, content in shop_content.get("dates", {}).items():
                data = content.get("data", {})

                row = {
                    "shop_id": shop_id,
                    "timestamp": data.get("dt"),
                    "count_in": float(data.get("count_in") or 0),
                    "conversion_rate": float(data.get("conversion_rate") or 0),
                    "turnover": float(data.get("turnover") or 0),
                    "sales_per_visitor": float(data.get("sales_per_visitor") or 0),
                }
                rows.append(row)

    df = pd.DataFrame(rows)

    # ✅ Format timestamp
    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df
