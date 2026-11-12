import pandas as pd
import json
import os

def save_statistics(data, output_path, summary_path, consumption_ranges = {"low": (1, 5), "medium": (5, 15), "high": (15, 25)}):
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
            "installation_type": meter_data["installation_type"].iloc[0]
        })

    # calculate individual statistics
    statistics = pd.DataFrame(statistics).round(5)

    # save individual statistics
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    statistics.to_csv(output_path, index=False)

    # count meters by installation type
    installation_counts = statistics["installation_type"].value_counts().to_dict()

    # classify meters according to maximum active power
    def classify_consumption(value):
        for i, (range_name, (lower, upper)) in enumerate(consumption_ranges.items()):
            if lower <= value < upper or (i == len(consumption_ranges) - 1 and value == upper):
                return range_name
        return "outside_ranges"

    statistics["consumption_range"] = statistics["kw_max"].apply(
        classify_consumption
    )

    range_order = ["low", "medium", "high", "outside_ranges"]

    # count meters by consumption range
    consumption_counts = statistics["consumption_range"].value_counts().reindex(range_order, fill_value=0).to_dict()

    # count meters by installation type and consumption range
    installation_consumption_counts = (
        statistics.groupby(["installation_type", "consumption_range"]).size().unstack(fill_value=0).reindex(columns=range_order, fill_value=0).to_dict(orient="index"))

    # format consumption ranges
    formatted_ranges = {
        name: f"{lower}-{upper} kW"
        for name, (lower, upper) in consumption_ranges.items()
    }

    # create summary
    summary = {
        "ranges": formatted_ranges,
        "total_meters": len(statistics),
        "installation_type_counts": installation_counts,
        "kw_max_range_counts": consumption_counts,
        "installation_type_by_kw_max_range": installation_consumption_counts
    }

    # save summary as json
    summary_dir = os.path.dirname(summary_path)
    if summary_dir:
        os.makedirs(summary_dir, exist_ok=True)

    with open(summary_path, "w") as file:
        json.dump(summary, file, indent=4)

    return statistics, summary