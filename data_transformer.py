import pandas as pd

def normalize_vemcount_response(response_json: dict) -> pd.DataFrame:
    rows = []

    # Detecteer of de root een shop_id is (oude format) of een datum-key (nieuwe format)
    for outer_key, outer_value in response_json.items():
        if outer_key.startswith("date_"):  # Nieuwe structuur
            for shop_id_str, shop_data in outer_value.items():
                shop_id = int(shop_id_str)
                dates = shop_data.get("dates", {})
                for timestamp_label, point in dates.items():
                    data = point.get("data", {})
                    rows.append({
                        "shop_id": shop_id,
                        "timestamp": pd.to_datetime(data.get("dt")),
                        "count_in": float(data.get("count_in", 0)),
                        "conversion_rate": float(data.get("conversion_rate", 0)),
                        "turnover": float(data.get("turnover", 0)),
                        "sales_per_visitor": float(data.get("sales_per_visitor", 0)),
                    })
        else:  # Oude structuur
            shop_id = int(outer_key)
            shop_data = outer_value
            dates = shop_data.get("dates", {})
            for date_label, day_info in dates.items():
                data = day_info.get("data", {})
                rows.append({
                    "shop_id": shop_id,
                    "timestamp": pd.to_datetime(data.get("dt")),
                    "count_in": float(data.get("count_in", 0)),
                    "conversion_rate": float(data.get("conversion_rate", 0)),
                    "turnover": float(data.get("turnover", 0)),
                    "sales_per_transaction": float(data.get("sales_per_transaction", 0)),
                })

    df = pd.DataFrame(rows)
    return df
