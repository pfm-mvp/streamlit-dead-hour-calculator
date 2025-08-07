import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    # 👉 Detecteer of data in 'date_YYYY-MM-DD' structuur zit (hourly) of normale structuur (daily)
    if "data" in response_json:
        # Nieuwe structuur (hourly): response_json["data"]["date_YYYY-MM-DD"][shop_id]["dates"]["Label"]["data"]
        for date_key, shops in response_json["data"].items():
            for shop_id, content in shops.items():
                dates = content.get("dates", {})
                for label, hour_block in dates.items():
                    data = hour_block.get("data", {})
                    rows.append({
                        "shop_id": int(shop_id),
                        "timestamp": pd.to_datetime(data.get("dt")),
                        "count_in": float(data.get("count_in") or 0),
                        "conversion_rate": float(data.get("conversion_rate") or 0),
                        "turnover": float(data.get("turnover") or 0),
                        "sales_per_visitor": float(data.get("sales_per_visitor") or 0),
                    })
    else:
        # Oude structuur (daily): response_json[shop_id]["dates"]["Label"]["data"]
        for shop_id, shop_content in response_json.items():
            dates = shop_content.get("dates", {})
            for date_label, day_info in dates.items():
                data = day_info.get("data", {})
                rows.append({
                    "shop_id": int(shop_id),
                    "timestamp": pd.to_datetime(data.get("dt")),
                    "count_in": float(data.get("count_in") or 0),
                    "conversion_rate": float(data.get("conversion_rate") or 0),
                    "turnover": float(data.get("turnover") or 0),
                    "sales_per_transaction": float(data.get("sales_per_transaction") or 0),
                })

    df = pd.DataFrame(rows)
    return df
