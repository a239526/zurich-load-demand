import pandas as pd

def save_meter_statistics(data, output_path):
    statistics = []

    for meter_id, meter_data in data.items():
        statistics.append({
            "meter_id": meter_id,
            "kw_mean": meter_data["kW"].mean(),
            "kw_max": meter_data["kW"].max(),
            "kw_min": meter_data["kW"].min(),
            "kvar_mean": meter_data["kvar"].mean(),
            "kvar_max": meter_data["kvar"].max(),
            "kvar_min": meter_data["kvar"].min(),
            "installation_type": meter_data["installation_type"].iloc[0]  # Assuming installation_type is consistent for each meter
        })

    statistics = pd.DataFrame(statistics).round(5)
    statistics.to_csv(output_path, index=False)

    return statistics