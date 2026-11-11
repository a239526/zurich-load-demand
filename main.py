from create_parquet import save_processed_data

PROCESSED_PATH = "outputs/smart_meter_data.parquet"

# parameters for dataset filtering
AVAILABLE_DATA_THRESHOLD = 0.95
INSTALLATION_TYPES = ['Single-family house', 'Common areas', 'Apartment'] #["Single-family house", "Common areas", "Heat pump", "Underground garage", "EV charging station", "Apartment"]

if __name__ == "__main__":
    # creates parquet files
    save_processed_data(AVAILABLE_DATA_THRESHOLD, INSTALLATION_TYPES, PROCESSED_PATH)