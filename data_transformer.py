import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    # 🔍 Check of dit een geneste structuur is met "data" als hoofdlaag
    if "data" in response_json:
        # ✅ Diep geneste structuur parseren (zoals gebruikt in Dead Hour Optimizer)
        for date_block in response_json["data"].values():
            for shop_content in date_block.values():
                shop_id = shop_content.get("data", {}).get("id")
                for _, day_info in shop_content.get("dates", {}).items():
                    data = day_info.get("data", {})
                    row = {
                        "shop_id": int(shop_id) if shop_id else None,
                        "timestamp": data.get("dt"),
                        "turnover": float(data.get("turnover", 0)),
                        "count_in": float(data.get("count_in", 0)),
                        "conversion_rate": float(data.get("conversion_rate", 0)),
                        "sales_per_visitor": float(data.get("sales_per_visitor") or 0),
                    }
                    rows.append(row)
    else:
        # ✅ Oude structuur (zoals gebruikt in Saturday ROI Calculator)
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

    # ✅ Zet datumkolommen om naar datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df
