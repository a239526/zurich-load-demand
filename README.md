
# Electricity Demand Generation

## Overview

This repository provides Python scripts to process residential smart meter data and generate electricity demand profiles for distribution network test cases.

The scripts use measured electricity consumption profiles to generate active and reactive power demand at **15-minute intervals**. Individual meter profiles are normalized and subsequently scaled according to randomly generated maximum active power values, allowing different residential consumption levels to be represented.

The repository currently supports four distribution network cases: case5, case13, case34 and case123, where the number represents the amount of buses.

For each case, the number of low-, medium-, and high-consumption households assigned to each bus is defined in a JSON configuration file.

The demand generation supports two configurations:

- **Balanced:** All selected meter profiles are aggregated into a single active and reactive power profile for each bus.
- **Unbalanced:** Each selected meter is randomly assigned to one of three phases (a, b, or c), and the profiles are aggregated separately for each phase.

Additionally, the scripts generate meter statistics and save the allocation of selected meters and their corresponding maximum power scaling factors for each bus and phase.

## Data Source

The smart meter data used in this repository comes from:

Kaiser, K., Kreft, M., González Vayá, M., & Hug, H. (2026). *Dataset on residential electricity load profiles in Switzerland* (Version v1) [Dataset]. Zenodo. [https://doi.org/10.5281/zenodo.21398769](https://doi.org/10.5281/zenodo.21398769)

The original dataset contains residential electricity measurements at 15-minute intervals, together with metadata describing the meters and their installation types.

Active and reactive power are calculated from the measured energy values. The resulting power profiles are expressed in kW and kvar, respectively.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/a239526/zurich-load-demand
cd zurich-load-demand
```

### 2. Create and activate a virtual environment

Create the virtual environment:

```bash
python -m venv .venv
```

Activate it:

**Windows (PowerShell):**

```bash
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the main script

Adjust the parameters in `main.py` according to the desired processing and demand generation settings.

Run the main script:

```bash
python main.py
```

The script processes the smart meter data, calculates meter statistics, filters the available profiles, and generates the demand CSV and meter allocation JSON files for each selected case.

## Configuration

The generation process can be configured directly in `main.py`.

### General configuration

```python
PROCESSED_PATH = "outputs/smart_meter_data.parquet"

CREATE_PARQUET = False
AVAILABLE_DATA_THRESHOLD = 0.95
INSTALLATION_TYPES = ["Single-family house", "Common areas", "Apartment"]

CASES = [5, 13, 34, 123]
UNBALANCED = True
```

The parameters can be adjusted as follows:

| **Parameter**          | **Description**                                                                                                                                                                               |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PROCESSED_PATH`           | Path where the processed smart meter data is saved and loaded.                                                                                                                                      |
| `CREATE_PARQUET`           | If `True`, processes the original meter CSV files and creates the Parquet file. If `False`, loads the existing Parquet file.                                                                    |
| `AVAILABLE_DATA_THRESHOLD` | Minimum proportion of available data points required for a meter to be selected. For example, `0.95` retains meters with at least 95% of the maximum number of data points found in the metadata. |
| `INSTALLATION_TYPES`       | List of installation types to retain during metadata filtering.                                                                                                                                     |
| `CASES`                    | List of distribution network cases to process. Supported values are `5`, `13`, `34`, and `123`.                                                                                             |
| `UNBALANCED`               | If `True`, generates separate demand profiles for each phase. If `False`, generates one aggregated profile per bus.                                                                             |

To create the Parquet file from the original dataset, set:

```python
CREATE_PARQUET = True
```

After the file has been generated, it can be reused in subsequent executions by setting:

```python
CREATE_PARQUET = False
```

This avoids loading and processing all original meter CSV files every time the script is executed.

The `CASES` parameter accepts multiple cases, which are processed sequentially. For example:

```python
CASES = [5, 13, 34, 123]
```

To process only one case:

```python
CASES = [34]
```

### Demand configuration

The number of households assigned to each bus is defined in a separate `bus_config.json` file for each case.

The configuration files are stored in the `cases/` directory:

```text
cases/
├── case5/
│   └── bus_config.json
├── case13/
│   └── bus_config.json
├── case34/
│   └── bus_config.json
└── case123/
    └── bus_config.json
```

Each file specifies the number of low-, medium-, and high-consumption households for every bus.

For example:

```json
{
    "bus_002": {"n_low": 9, "n_medium": 5, "n_high": 3},
    "bus_003": {"n_low": 4, "n_medium": 9, "n_high": 5}
}
```

A bus can have zero assigned meters. In this case, it is skipped during demand generation and does not produce columns in the output CSV.

### Consumption ranges and random seeds

The consumption categories are associated with the following maximum active power ranges, defined in `create_demand_csv.py`:

```python
CONSUMPTION_RANGES = {
    "low": (1, 5),
    "medium": (5, 15),
    "high": (15, 25)
}
```

For each selected meter, a maximum active power value is randomly generated using a uniform distribution within the corresponding range. This value is used as the scaling factor for both active and reactive power profiles.

Three independent random seeds control meter selection, maximum power generation, and phase assignment:

```python
SEED_METER = 42
SEED_CONSUMPTION = 123
SEED_PHASE = 456
```

The random number generators are initialized inside `create_demand_csv()`. Therefore, repeated calls with the same inputs and configuration produce reproducible results.

## Data Processing

The processing pipeline is divided into four main steps.

### 1. Smart meter selection and loading

The `create_parquet.py` script filters the original metadata according to the available data threshold and installation types.

The filtering procedure is performed as follows:

- The maximum number of available data points among all meters is identified.
- A minimum number of data points is calculated using `AVAILABLE_DATA_THRESHOLD`. Meters below this threshold are discarded.
- Meters whose installation types are not included in `INSTALLATION_TYPES` are discarded.

The selected meter CSV files are then loaded and processed.

Active and reactive energy are calculated using the original energy measurements:

- Active energy (`kWh`) is calculated as the energy consumed from the grid minus the energy exported to the grid.
- Reactive energy (`kvarh`) is calculated as the reactive energy exported to the grid minus the reactive energy imported from the grid.

Since the measurements are provided at 15-minute intervals, energy values are multiplied by four to obtain average power:

- `kW = kWh × 4`
- `kvar = kvarh × 4`

The processed meter profiles are combined into a single Parquet file, including the meter ID and installation type.

### 2. Meter statistics

The `meter_statistics.py` script calculates individual statistics for each selected meter.

The following quantities are calculated:

- Mean, maximum, and minimum active power (`kW`).
- Mean, maximum, and minimum reactive power (`kvar`).
- Installation type.

Meters are also classified according to their maximum active power using the consumption ranges defined in the script.

The statistics are summarized by installation type and consumption range.

### 3. Data normalization and filtering

The `data_treatment.py` script normalizes the active and reactive power profiles of each meter.

Both quantities are divided by the maximum active power of the corresponding meter:

$$
P_{\mathrm{norm}}(t) = \frac{P(t)}{P_{\max}}
$$

$$
Q_{\mathrm{norm}}(t) = \frac{Q(t)}{P_{\max}}
$$

This normalization preserves the relationship between active and reactive power while setting the maximum active power of each profile to one.

After normalization, meters are filtered according to their average daytime and nighttime active power consumption.

The periods are defined as follows:

- **Daytime:** 08:00 to 20:00.
- **Nighttime:** 20:00 to 08:00.

Only meters with higher average daytime consumption than nighttime consumption are retained for demand generation.

### 4. Demand generation

The `create_demand_csv.py` script generates the demand profiles using the normalized meter data and the bus configurations.

For each bus:

- The required number of meters is selected randomly from the available filtered meters, without replacement within that bus.
- Each selected meter is assigned a consumption category according to the bus configuration.
- A maximum active power value is randomly generated within the corresponding consumption range.
- The normalized active and reactive power profiles are multiplied by this value.
- The resulting profiles are aggregated by timestamp.

For the balanced configuration, all selected meter profiles are aggregated into one active and reactive power profile per bus.

For the unbalanced configuration, each selected meter is randomly assigned to phase a, b, or c. The profiles are then aggregated separately for each phase.

If a phase receives no meters, its active and reactive power profiles are set to zero. However, if an entire bus receives no meters, it is skipped and no columns are generated for that bus.

The script also records the meter IDs, consumption categories, and maximum power scaling factors associated with each bus and phase.

## Output

Generated files are saved in the `outputs/` directory, which is created automatically if it does not already exist.

### Processed smart meter data

The processed meter data is saved as a single Parquet file:

```text
outputs/
└── smart_meter_data.parquet
```

The file contains the following columns:

| **Column**      | **Description**                        |
| --------------------- | -------------------------------------------- |
| `timestamp`         | Timestamp of the power measurement.          |
| `kW`                | Active power in kW.                          |
| `kvar`              | Reactive power in kvar.                      |
| `installation_type` | Installation type associated with the meter. |
| `meter_id`          | Unique meter identifier.                     |

The `read_processed_data()` function loads this file and reconstructs a dictionary in which each meter ID is associated with its corresponding DataFrame.

### Meter statistics

The `save_statistics()` function generates two files:

```text
outputs/
├── meter_statistics.csv
└── statistics_summary.json
```

The `meter_statistics.csv` file contains the individual statistics calculated for each meter, including its mean, maximum, and minimum active and reactive power, installation type, and maximum active power consumption category.

The `statistics_summary.json` file contains aggregated statistics, including:

- Total number of meters.
- Number of meters per installation type.
- Number of meters per maximum active power range.
- Number of meters per installation type and maximum active power range.
- Consumption ranges used for classification.

### Demand CSV files

Demand files are saved in a separate directory for each case, using the following naming convention:

```text
outputs/
├── case5/
│   ├── balanced_demand.csv
│   └── balanced_demand_meter_allocation.json
├── case13/
│   ├── unbalanced_demand.csv
│   └── unbalanced_demand_meter_allocation.json
├── case34/
│   ├── unbalanced_demand.csv
│   └── unbalanced_demand_meter_allocation.json
└── case123/
    ├── unbalanced_demand.csv
    └── unbalanced_demand_meter_allocation.json
```

The example above illustrates the output structure when different configurations are generated for different cases. The actual files depend on the values defined in `CASES` and `UNBALANCED`.

Each CSV contains one row per timestamp and separate columns for the active and reactive power of each bus or phase.

**Balanced configuration**

Each bus with assigned meters generates two columns:

- `Pbus_<bus_id>`: Active power in kW.
- `Qbus_<bus_id>`: Reactive power in kvar.

For example:

```text
timestamp,Pbus_002,Qbus_002,Pbus_003,Qbus_003
2023-01-01 00:00:00,12.45,3.21,8.32,2.14
2023-01-01 00:15:00,13.10,3.45,9.01,2.36
2023-01-01 00:30:00,14.25,3.82,8.75,2.28
```

**Unbalanced configuration**

Each bus with assigned meters generates six columns, corresponding to the active and reactive power of its three phases:

- `Pbus_<bus_id>_a` and `Qbus_<bus_id>_a`.
- `Pbus_<bus_id>_b` and `Qbus_<bus_id>_b`.
- `Pbus_<bus_id>_c` and `Qbus_<bus_id>_c`.

For example:

```text
timestamp,Pbus_002_a,Qbus_002_a,Pbus_002_b,Qbus_002_b,Pbus_002_c,Qbus_002_c
2023-01-01 00:00:00,4.25,1.10,3.80,0.95,4.40,1.16
2023-01-01 00:15:00,4.60,1.25,4.10,1.02,4.40,1.18
2023-01-01 00:30:00,4.80,1.32,4.25,1.10,4.65,1.22
```

If a phase receives no meters, its corresponding columns are still generated with zero values. Buses with no assigned meters are omitted entirely.

### Meter allocation JSON

Alongside each demand CSV, a JSON file is generated to record the meter allocation and scaling factors used during demand generation.

The JSON file follows the same base name as the demand CSV, with the suffix `_meter_allocation.json`.

For example:

```text
outputs/
└── case34/
    ├── unbalanced_demand.csv
    └── unbalanced_demand_meter_allocation.json
```

Each entry contains the following information:

| **Field**      | **Description**                                                                                                                            |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `meter_id`         | Identifier of the selected smart meter.                                                                                                          |
| `max_power`        | Maximum active power assigned to the meter, in kW. This is also the scaling factor applied to its normalized active and reactive power profiles. |
| `consumption_type` | Consumption category assigned to the meter (`low`, `medium`, or `high`).                                                                   |

For the balanced configuration, meters are grouped directly by bus:

```json
{
    "bus_002": [
        {
            "meter_id": 125,
            "max_power": 3.45,
            "consumption_type": "low"
        },
        {
            "meter_id": 238,
            "max_power": 12.8,
            "consumption_type": "medium"
        }
    ]
}
```

For the unbalanced configuration, meters are grouped by bus and phase:

```json
{
    "bus_002": {
        "a": [
            {
                "meter_id": 125,
                "max_power": 3.45,
                "consumption_type": "low"
            }
        ],
        "b": [],
        "c": [
            {
                "meter_id": 238,
                "max_power": 12.8,
                "consumption_type": "medium"
            }
        ]
    }
}
```

This file allows the generated demand profiles to be traced back to the original smart meters and their corresponding scaling factors.

## Repository Structure

```text
zurich-load-demand/
│
├── cases/
│   ├── case5/
│   │   └── bus_config.json
│   ├── case13/
│   │   └── bus_config.json
│   ├── case34/
│   │   └── bus_config.json
│   └── case123/
│       └── bus_config.json
│
├── dataset/
│   ├── smart_meter_data/
│   └── metadata.csv
│
├── outputs/
│   ├── smart_meter_data.parquet
│   ├── meter_statistics.csv
│   ├── statistics_summary.json
│   ├── case5/
│   ├── case13/
│   ├── case34/
│   └── case123/
│
├── create_parquet.py       # Loads and processes the original smart meter data
├── meter_statistics.py     # Calculates individual and aggregated meter statistics
├── data_treatment.py       # Normalizes and filters meter profiles
├── create_demand_csv.py    # Generates synthetic demand profiles and meter allocation files
├── main.py                 # Main script and general configuration
│
├── requirements.txt        # Python dependencies
├── .gitignore
└── README.md
```

## Notes

- Original smart meter measurements are provided as energy values. Active and reactive power are calculated by multiplying the corresponding 15-minute energy values by four.
- The meter selection process is performed without replacement within each bus. However, the same meter may be selected for different buses.
- Maximum active power values are generated independently for each selected meter using a uniform distribution within its assigned consumption range.
- The same scaling factor is applied to both active and reactive power profiles, so that power factor is preserved.
- The random seeds ensure reproducibility of meter selection, maximum power generation, and phase assignment.
- In the unbalanced configuration, meter phases are assigned randomly and independently. Therefore, the number of meters assigned to each phase may differ.
- Buses with zero assigned meters are omitted from the demand CSV. Phases without meters are retained with zero demand when their bus has at least one assigned meter.
- The meter allocation JSON records the selected meter IDs, consumption categories, and maximum power scaling factors, allowing the generated demand profiles to be traced back to their source profiles.
- The Parquet file can be reused in subsequent executions by setting `CREATE_PARQUET = False`.

## Citation

If you use the dataset or the generated demand profiles in your research, please cite the original dataset:

Kaiser, K., Kreft, M., González Vayá, M., & Hug, H. (2026). *Dataset on residential electricity load profiles in Switzerland* (Version v1) [Dataset]. Zenodo. [https://doi.org/10.5281/zenodo.21398769](https://doi.org/10.5281/zenodo.21398769)
