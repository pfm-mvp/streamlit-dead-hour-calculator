import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    # 🔁 Loop over top-level shop-IDs
    for shop_id, shop_content in response_json.items():
        # 🧪 Check of er een 'dates'-laag is
        if "dates" in shop_content:
            dates_dict = shop_content["dates"]
            for timestamp_label, hour_info in dates_dict.items():
                data = hour_info.get("data", {})
                row = {
                    "shop_id": int(shop_id),
                    "timestamp": data.get("dt"),
                    "turnover": float(data.get("turnover") or 0),
                    "count_in": float(data.get("count_in") or 0),
                    "conversion_rate": float(data.get("conversion_rate") or 0),
                    "sales_per_visitor": float(data.get("sales_per_visitor") or 0),
                }
                rows.append(row)
        else:
            # 🧪 Val terug op oude structuur (zoals ROI calc)
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
    if not df.empty:
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

    return df
