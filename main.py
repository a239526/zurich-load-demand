from create_parquet import save_processed_data, read_processed_data
from meter_statistics import save_statistics
from data_treatment import normalize_data, filter_daytime_meters
from create_demand_csv import create_demand_csv
from generate_plots import plot_time_series, plot_daily_average, plot_daily_average_total
import json

PROCESSED_PATH = "outputs/smart_meter_data.parquet"

# parameters for parquet creation
CREATE_PARQUET = False  # set to True to create parquet files, False to read existing ones
AVAILABLE_DATA_THRESHOLD = 0.95
INSTALLATION_TYPES = ['Single-family house', 'Common areas', 'Apartment'] #["Single-family house", "Common areas", "Heat pump", "Underground garage", "EV charging station", "Apartment"]

# parameters for demand csv creation
CASES = [5, 13, 34, 123] # [5, 13, 34, 123] 
UNBALANCED = True # set to True to create unbalanced, False to create balanced demand profiles

# parameters for plot creation
GENERATE_PLOTS = True

if __name__ == "__main__":
    # creates parquet files
    if CREATE_PARQUET:
        save_processed_data(AVAILABLE_DATA_THRESHOLD, INSTALLATION_TYPES, PROCESSED_PATH)

    meters_id, data = read_processed_data(PROCESSED_PATH)
    meter_statistics, summary = save_statistics(data, "outputs/meter_statistics.csv", "outputs/statistics_summary.json")

    processed_meters, processed_data = filter_daytime_meters(normalize_data(data))

    for case in CASES:
        demand, meter_allocation = create_demand_csv(data=processed_data, adequate_meters=processed_meters, case=case, unbalanced=UNBALANCED)

    if GENERATE_PLOTS:
        for case in CASES:
            case_name = f"case{case}"

            with open(f"cases/{case_name}/bus_config.json") as file:
                bus_config = json.load(file)

            # Select the first bus with assigned meters
            first_bus = next(
                (bus for bus, config in bus_config.items() if sum(config.values()) > 0), None)

            if first_bus is not None:
                bus_number = int(first_bus.split("_")[1])

                plot_time_series(case, bus_number, UNBALANCED)
                plot_daily_average(case, bus_number, UNBALANCED)

            plot_daily_average_total(case, UNBALANCED)