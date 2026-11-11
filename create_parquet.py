import os
import pandas as pd
from tqdm import tqdm

DATA_PATH = "dataset/smart_meter_data"
METADATA_PATH = "dataset/metadata.csv"
PROCESSED_PATH = "outputs/smart_meter_data.parquet"

def filter_metadata(threshold=0.95, installation_types=None):
    # read metadata file
    metadata = pd.read_csv(METADATA_PATH, sep=";")
    metadata.columns = metadata.columns.str.strip()

    # get maximum amount of available data
    max_points = metadata["0_num_data_points"].max()

    # define tolerance for amount of available data
    min_points = threshold * max_points

    # filter by number of data points
    filtered_metadata = metadata[
        metadata["0_num_data_points"] >= min_points
    ].copy()

    # filter by installation type
    if installation_types is not None:
        filtered_metadata = filtered_metadata[
            filtered_metadata["0_installation_type"].isin(installation_types)
        ].copy()

    print(f"Filtered meters: {len(filtered_metadata)} / {len(metadata)}")

    return filtered_metadata


def load_smart_meter(meter_id, installation_type):
    # load the smart meter data for a given meter_id
    file_path = os.path.join(DATA_PATH, f"{meter_id}.csv")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"data file for meter_id {meter_id} not found.")

    df = pd.read_csv(file_path, sep=";")

    # convert timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp_utc"], utc=True)

    # calculate net energy
    df["kWh"] = df["kWh_to_installation"] - df["kWh_to_grid"]
    df["kvarh"] = df["kvarh_to_grid"] - df["kvarh_to_installation"]

    # convert energy to power (15-minute interval)
    df["kW"] = df["kWh"] * 4
    df["kvar"] = df["kvarh"] * 4

    # save installation type
    df["installation_type"] = installation_type

    # keep only necessary data
    df = df[["timestamp", "kW", "kvar", "installation_type"]]

    return df


def load_all_smart_meters(filtered_metadata):
    # load data for all selected meters
    data = {}

    for _, row in tqdm(
        filtered_metadata.iterrows(),
        total=len(filtered_metadata),
        desc="Loading smart meters"
    ):
        meter_id = int(row["0_meter_id"])
        installation_type = row["0_installation_type"]

        data[meter_id] = load_smart_meter(meter_id, installation_type)

    return data


def save_processed_data(threshold=0.95, installation_types=None, output_path=PROCESSED_PATH):

    # filter metadata
    filtered_metadata = filter_metadata(threshold=threshold, installation_types=installation_types)

    if filtered_metadata.empty:
        raise ValueError("No smart meters match the specified filters.")

    # load data for all selected meters
    data = load_all_smart_meters(filtered_metadata)

    # add meter_id to each dataframe and combine all meters
    dfs = []

    for meter_id, df in data.items():
        df = df.copy()
        df["meter_id"] = meter_id
        dfs.append(df)

    combined_data = pd.concat(dfs, ignore_index=True)

    # create the output directory if necessary
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # save as parquet
    combined_data.to_parquet(output_path, index=False)

    print(f"Processed data saved to: {output_path}")

    return combined_data