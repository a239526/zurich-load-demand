from create_parquet import save_processed_data, read_processed_data
from meter_statistics import save_meter_statistics

PROCESSED_PATH = "outputs/smart_meter_data.parquet"

# parameters for parquet creation
CREATE_PARQUET = False  # set to True to create parquet files, False to read existing ones
AVAILABLE_DATA_THRESHOLD = 0.95
INSTALLATION_TYPES = ['Single-family house', 'Common areas', 'Apartment'] #["Single-family house", "Common areas", "Heat pump", "Underground garage", "EV charging station", "Apartment"]

if __name__ == "__main__":
    # creates parquet files
    if CREATE_PARQUET:
        save_processed_data(AVAILABLE_DATA_THRESHOLD, INSTALLATION_TYPES, PROCESSED_PATH)

    meters_id, data = read_processed_data(PROCESSED_PATH)
    meter_statistics = save_meter_statistics(data, "outputs/meter_statistics.csv")