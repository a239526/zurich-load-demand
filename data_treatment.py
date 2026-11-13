def normalize_data(data):
    normalized_data = {}

    for meter_id, meter_data in data.items():
        normalized_meter = meter_data.copy()

        max_kw = normalized_meter["kW"].max()

        # Normalize kW and kvar values by dividing by the maximum kW value
        normalized_meter["kW"] = normalized_meter["kW"] / max_kw
        normalized_meter["kvar"] = normalized_meter["kvar"] / max_kw

        normalized_data[meter_id] = normalized_meter

    return normalized_data

def filter_daytime_meters(data):
    adequate_meters = []
    filtered_data = {}

    for meter_id, meter_data in data.items():
        meter_data = meter_data.copy()

        # Extract the hour from the timestamp
        meter_data["time"] = meter_data["timestamp"].dt.hour

        # Define daytime and nighttime periods
        daytime = meter_data[(meter_data["time"] >= 8) & (meter_data["time"] < 20)]
        nighttime = meter_data[(meter_data["time"] >= 20) | (meter_data["time"] < 8)]

        # Calculate the average kW consumption for each period
        daytime_mean = daytime["kW"].mean()
        nighttime_mean = nighttime["kW"].mean()

        # Filter the adequate meters
        if daytime_mean > nighttime_mean:
            adequate_meters.append(meter_id)
            filtered_data[meter_id] = meter_data.drop(columns="time").reset_index(drop=True)

    print(f"Number of filtered meters: {len(adequate_meters)}")

    return adequate_meters, filtered_data