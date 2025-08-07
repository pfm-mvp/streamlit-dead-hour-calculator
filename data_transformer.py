import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    for outer_key, outer_value in response_json.items():
        if "dates" in outer_value:  # Oude structuur per shop_id
            shop_id = int(outer_key)
            dates = outer_value["dates"]
            for date_label, entry in dates.items():
                data = entry.get("data", {})
                rows.append({
                    "shop_id": shop_id,
                    "timestamp": data.get("dt"),
                    "turnover": float(data.get("turnover") or 0),
                    "count_in": float(data.get("count_in") or 0),
                    "conversion_rate": float(data.get("conversion_rate") or 0),
                    "sales_per_visitor": float(data.get("sales_per_visitor") or 0),
                    "sales_per_transaction": float(data.get("sales_per_transaction") or 0),
                })

        elif outer_key.startswith("date_"):  # Nieuwe structuur met "date_2025-08-01" → {shop_id → {dates}}
            date_part = outer_key.replace("date_", "")
            shops_dict = outer_value
            for shop_id_str, shop_data in shops_dict.items():
                shop_id = int(shop_id_str)
                dates = shop_data.get("dates", {})
                for _, entry in dates.items():
                    data = entry.get("data", {})
                    rows.append({
                        "shop_id": shop_id,
                        "timestamp": data.get("dt"),
                        "turnover": float(data.get("turnover") or 0),
                        "count_in": float(data.get("count_in") or 0),
                        "conversion_rate": float(data.get("conversion_rate") or 0),
                        "sales_per_visitor": float(data.get("sales_per_visitor") or 0),
                        "sales_per_transaction": float(data.get("sales_per_transaction") or 0),
                    })

    df = pd.DataFrame(rows)
    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df
