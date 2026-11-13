import os
import json
import numpy as np
import pandas as pd

# random seeds
SEED_METER = 42
SEED_CONSUMPTION = 123
SEED_PHASE = 234

# consumption ranges in kW
CONSUMPTION_RANGES = {"low": (1, 5), "medium": (5, 15), "high": (15, 25)}

# available phases
PHASES = ["a", "b", "c"]
CASES_PATH = "cases"


def select_meters(adequate_meters, n_meters, rng):
    # randomly select meters without replacement
    if n_meters > len(adequate_meters):
        raise ValueError(f"Not enough adequate meters: requested {n_meters}, but only {len(adequate_meters)} are available.")
    return rng.choice(adequate_meters, size=n_meters, replace=False).tolist()


def assign_consumption_types(n_low, n_medium, n_high):
    # create a list with the specified number of each consumption type
    return ["low"] * n_low + ["medium"] * n_medium + ["high"] * n_high


def generate_max_power(consumption_type, rng):
    # randomly generate the maximum active power within the specified range
    lower, upper = CONSUMPTION_RANGES[consumption_type]
    return rng.uniform(lower, upper)


def aggregate_profiles(profiles, timestamps):
    # aggregate active and reactive power from all selected profiles
    if not profiles:
        return pd.DataFrame({"timestamp": timestamps, "kW": 0.0, "kvar": 0.0})
    return pd.concat(profiles).groupby("timestamp")[["kW", "kvar"]].sum().reset_index()


def create_bus_load(data, adequate_meters, config, rng_meter, rng_consumption, rng_phase, unbalanced=False):
    # get the number of houses of each consumption type
    n_low, n_medium, n_high = config["n_low"], config["n_medium"], config["n_high"]
    n_meters = n_low + n_medium + n_high

    # randomly select meters and assign consumption types
    meters = select_meters(adequate_meters, n_meters, rng_meter)
    consumption_types = assign_consumption_types(n_low, n_medium, n_high)

    # initialize profile lists and meter allocation
    profiles = {phase: [] for phase in PHASES} if unbalanced else []
    allocation = {phase: [] for phase in PHASES} if unbalanced else []

    # generate and scale each meter profile
    for meter_id, consumption_type in zip(meters, consumption_types):
        max_power = generate_max_power(consumption_type, rng_consumption)
        profile = data[meter_id][["timestamp", "kW", "kvar"]].copy()
        profile[["kW", "kvar"]] *= max_power

        phase = rng_phase.choice(PHASES) if unbalanced else None
        profiles[phase].append(profile) if unbalanced else profiles.append(profile)

        meter_info = {"meter_id": int(meter_id), "max_power": float(max_power), "consumption_type": consumption_type}
        if unbalanced:
            allocation[phase].append(meter_info)
        else:
            allocation.append(meter_info)

    # aggregate profiles and return meter allocation
    if not unbalanced:
        return aggregate_profiles(profiles, data[next(iter(data))]["timestamp"]), allocation

    phase_profiles = {phase: aggregate_profiles(profiles[phase], data[next(iter(data))]["timestamp"]) for phase in PHASES}
    return phase_profiles, allocation


def create_demand_csv(data, adequate_meters, case, unbalanced=False, output_path=None):
    # initialize random number generators
    rng_meter, rng_consumption, rng_phase = np.random.default_rng(SEED_METER), np.random.default_rng(SEED_CONSUMPTION), np.random.default_rng(SEED_PHASE)

    # get case name and load bus configuration
    case_name = str(case) if str(case).startswith("case") else f"case{case}"
    config_path = os.path.join(CASES_PATH, case_name, "bus_config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Bus configuration not found: {config_path}")

    with open(config_path, "r") as file:
        bus_config = json.load(file)

    # define output path
    if output_path is None:
        balance_type = "unbalanced" if unbalanced else "balanced"
        output_path = os.path.join("outputs", f"{case_name}", f"{balance_type}_demand.csv")

    # create demand profiles and meter allocation
    bus_profiles, meter_allocation = [], {}

    for bus, config in bus_config.items():

        # skip buses with no meters
        if sum(config.values()) == 0:
            continue

        profile, allocation = create_bus_load(data, adequate_meters, config, rng_meter, rng_consumption, rng_phase, unbalanced)
        meter_allocation[bus] = allocation

        if unbalanced:
            for phase in PHASES:
                bus_profiles.append(profile[phase].rename(columns={"kW": f"P{bus}_{phase}", "kvar": f"Q{bus}_{phase}"}))
        else:
            bus_profiles.append(profile.rename(columns={"kW": f"P{bus}", "kvar": f"Q{bus}"}))

    # combine all bus profiles using timestamps
    demand = bus_profiles[0]
    for profile in bus_profiles[1:]:
        demand = demand.merge(profile, on="timestamp", how="outer")

    demand = demand.sort_values("timestamp").reset_index(drop=True)

    # create output directory and save demand
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    demand.to_csv(output_path, index=False)

    # save meter allocation
    allocation_path = os.path.splitext(output_path)[0] + "_meter_allocation.json"
    with open(allocation_path, "w") as file:
        json.dump(meter_allocation, file, indent=4)

    print(f"Demand data saved to: {output_path}")

    return demand, meter_allocation