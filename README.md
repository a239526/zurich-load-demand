
# Electricity Demand Generation

## Overview

This repository provides Python scripts to process residential smart meter data and generate active and reactive power demand profiles for distribution network test cases.

The generated profiles have a 15-minute resolution and are available in two configurations:

- **Balanced:** All selected meter profiles are aggregated into one demand profile per bus.
- **Unbalanced:** Meters are randomly assigned to phases (a, b, or c), and demand is aggregated separately for each phase.

The repository includes configurations for four distribution network cases: case5, case13, case34, and case123. Custom cases can also be added by creating a corresponding bus configuration.

Additionally, the scripts generate meter statistics, save the allocation of selected meters and their corresponding maximum power scaling factors for each bus and phase, and generate plots to visualize the resulting demand profiles.

## Data Source

The smart meter data comes from:

Kaiser, K., Kreft, M., González Vayá, M., & Hug, H. (2026). *Dataset on residential electricity load profiles in Switzerland* (Version v1) [Dataset]. Zenodo. [https://doi.org/10.5281/zenodo.21398769](https://doi.org/10.5281/zenodo.21398769)

The original dataset contains residential electricity measurements at 15-minute intervals, along with metadata describing the meters and their installation types.

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/a239526/zurich-load-demand
   cd zurich-load-demand
   ```
2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   **Windows (PowerShell):**

   ```bash
   .\.venv\Scripts\Activate.ps1
   ```

   **Linux / macOS:**

   ```bash
   source .venv/bin/activate
   ```
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Configure `main.py` and run:

   ```bash
   python main.py
   ```

The script processes the smart meter data, calculates meter statistics, filters the available profiles, and generates the demand CSV and meter allocation JSON files for each selected case. It can also generate plots of the resulting demand profiles.

## Configuration

The main parameters are defined in `main.py`:

```python
PROCESSED_PATH = "outputs/smart_meter_data.parquet"

CREATE_PARQUET = False
AVAILABLE_DATA_THRESHOLD = 0.95
INSTALLATION_TYPES = ["Single-family house", "Common areas", "Apartment"]

CASES = [5, 13, 34, 123]
UNBALANCED = True
GENERATE_PLOTS = True
```

| Parameter                    | Description                                                                                                                                                                                         |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PROCESSED_PATH`           | Path used to save and load the processed smart meter data.                                                                                                                                          |
| `CREATE_PARQUET`           | Set to `True` to process the original dataset and create the Parquet file. Set to `False` to reuse an existing file.                                                                            |
| `AVAILABLE_DATA_THRESHOLD` | Minimum proportion of available data points required for a meter to be selected. For example, `0.95` retains meters with at least 95% of the maximum number of data points found in the metadata. |
| `INSTALLATION_TYPES`       | List of installation types to retain during metadata filtering.                                                                                                                                     |
| `CASES`                    | List of network cases to generate demand for. Current supported values are `5`, `13`, `34`, and `123`.                                                                                      |
| `UNBALANCED`               | If `True`, generates separate demand profiles for each phase. If `False`, generates one aggregated profile per bus.                                                                             |
| `GENERATE_PLOTS`           | If `True`, generates and saves demand plots for each selected case.                                                                                                                               |

The Parquet file only needs to be created once using the desired threshold and installation types configuration. Afterward, set `CREATE_PARQUET = False` to avoid processing the original meter files again.

The `CASES` parameter accepts multiple cases, which are processed sequentially. For example:

```python
CASES = [5, 13, 34, 123]
```

### Bus configuration

Each case has a `bus_config.json` file under `cases/`. It defines the number of low-, medium-, and high-consumption meters assigned to each bus.

For example:

```json
{
    "bus_002": {"n_low": 9, "n_medium": 5, "n_high": 3},
    "bus_003": {"n_low": 4, "n_medium": 9, "n_high": 5}
}
```

The consumption categories correspond to the following maximum active power ranges in kW, defined in `create_demand_csv.py`:

```python
CONSUMPTION_RANGES = {
    "low": (1, 5),
    "medium": (5, 15),
    "high": (15, 25)
}
```

For each selected meter, a maximum active power value is randomly sampled from the corresponding range. This value scales both its normalized active and reactive power profiles.

### Creating a custom case

To generate demand for another distribution network, create a new folder under `cases/` and add a `bus_config.json` file.

For example, to add a case with 14 buses:

1. Create the folder `cases/case14/`.
2. Add `cases/case14/bus_config.json`, specifying the number of meters in each consumption category for every bus.

   ```json
   {
       "bus_002": {"n_low": 5, "n_medium": 3, "n_high": 2},
       "bus_003": {"n_low": 4, "n_medium": 6, "n_high": 1},
       "bus_004": {"n_low": 0, "n_medium": 2, "n_high": 1}
   }
   ```
3. Add the new case to `CASES` in `main.py`:

   ```python
   CASES = [14]
   ```

### Random seeds

Three independent seeds control meter selection, maximum power generation, and phase assignment:

```python
SEED_METER = 42
SEED_CONSUMPTION = 123
SEED_PHASE = 234
```

The random number generators are initialized inside `create_demand_csv()`, allowing reproducible results for repeated calls with the same inputs and configuration.

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

- The required number of meters is selected randomly from the available filtered normalized meters, without replacement within that bus.
- Each selected meter is assigned a consumption category according to the bus configuration.
- A maximum active power value is randomly generated within the corresponding consumption range.
- The normalized active and reactive power profiles are multiplied by this value.
- The resulting profiles are aggregated by timestamp.

For the balanced configuration, all selected meter profiles are aggregated into one active and reactive power profile per bus. For the unbalanced configuration, each selected meter is randomly assigned to phase a, b, or c. The profiles are then aggregated separately for each phase.

The script also records the meter IDs, consumption categories, and maximum power scaling factors associated with each bus and phase.

### 5. Demand visualization

The `generate_plots.py` script generates and saves plots from the demand CSV files created by `create_demand_csv.py`.

For each selected case, three plots are generated:

- **Bus time series:** Active and reactive power demand over the entire simulation period for the selected bus (in `main.py`, the first bus with assigned meters). The mean demand is also displayed.
- **Bus average daily profile:** Average active and reactive power demand at each time interval of the day for the same bus, including the mean values.
- **Total average daily profile:** Average total active and reactive power demand across all buses at each time interval of the day, including the mean values.

For unbalanced demand files, the individual bus plots show the sum of the three phases. The total demand plots also account for all phases.

Plots are generated when `GENERATE_PLOTS = True` in `main.py`. The `UNBALANCED` setting determines which demand CSV files are read.

All plots are saved in the corresponding `outputs/caseX/` folder.

## Outputs

All generated files are saved under `outputs/`. The directory is created automatically when needed.

| File                                                          | Description                                                                                                       |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `smart_meter_data.parquet`                                  | Processed smart meter profiles, including timestamps, active and reactive power, installation type, and meter ID. |
| `meter_statistics.csv`                                      | Individual statistics for each meter and its consumption category.                                                |
| `statistics_summary.json`                                   | Aggregated statistics by installation type and consumption category.                                              |
| `{case}/{balanced\|unbalanced}_demand.csv`                   | Generated demand profiles for each selected case.                                                                 |
| `{case}/{balanced\|unbalanced}_demand_meter_allocation.json` | Meter allocation and scaling factors used to generate the corresponding demand profiles.                          |
| `{case}/bus_<bus_id>_time_series.png`                       | Active and reactive power time series for the first bus with assigned meters.                                     |
| `{case}/bus_<bus_id>_daily_average.png`                     | Average daily active and reactive power profiles for the first bus with assigned meters.                          |
| `{case}/total_daily_average.png`                            | Average daily total active and reactive power profiles across all buses.                                          |

Each demand CSV contains one row per timestamp and separate columns for active and reactive power.

**Balanced configuration:** Each bus with assigned meters generates two columns, `Pbus_<bus_id>` and `Qbus_<bus_id>`.

**Unbalanced configuration:** Each bus with assigned meters generates six columns, corresponding to active and reactive power for phases a, b, and c. If a phase receives no meters, its columns are still generated with zero values. Buses with no assigned meters are omitted.

The meter allocation JSON records the selected meter IDs, their consumption categories, and their maximum active power scaling factors. In balanced cases, meters are grouped by bus; in unbalanced cases, they are grouped by bus and phase. This allows the generated profiles to be traced back to the original smart meter data.

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
├── generate_plots.py       # Generates and saves demand profile plots
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
