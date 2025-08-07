import pandas as pd

def normalize_vemcount_response(response_json):
    records = []

    for date_key, shop_data in response_json.get("data", {}).items():
        for shop_id, shop_info in shop_data.items():
            shop_metadata = shop_info.get("data", {})
            dates = shop_info.get("dates", {})

            for timestamp, ts_info in dates.items():
                row = {
                    "shop_id": shop_metadata.get("id"),
                    "shop_name": shop_metadata.get("name"),
                    "datetime": ts_info["data"].get("dt"),
                }

                # Voeg alle andere KPI's toe (zoals sales_per_visitor, conversion_rate, enz.)
                for kpi, value in ts_info["data"].items():
                    if kpi != "dt":
                        row[kpi] = float(value) if isinstance(value, str) and value.replace('.', '', 1).isdigit() else value

                records.append(row)

    df = pd.DataFrame(records)

    if not df.empty:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['hour'] = df['datetime'].dt.hour
        df['day'] = df['datetime'].dt.day_name()
        df = df.sort_values("datetime")

    return df
