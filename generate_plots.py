
import os
import pandas as pd
import matplotlib.pyplot as plt

# General configuration
OUTPUT_DIR = "outputs"
UNBALANCED = True

# Plot colors
LOAD_COLOR = "#F8A4C8"
MEAN_COLOR = "#C2185B"


def read_bus_demand(case, bus_number, unbalanced=UNBALANCED):
    """Read active and reactive power demand for a specific bus."""

    case_name = str(case) if str(case).startswith("case") else f"case{case}"
    balance_type = "unbalanced" if unbalanced else "balanced"
    file_path = os.path.join(OUTPUT_DIR, case_name, f"{balance_type}_demand.csv")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Demand file not found: {file_path}")

    bus = f"bus_{bus_number:03d}"
    df = pd.read_csv(file_path, parse_dates=["timestamp"])

    # Identify the columns associated with the selected bus
    if unbalanced:
        kw_columns = [col for col in df.columns if col.startswith(f"P{bus}_")]
        kvar_columns = [col for col in df.columns if col.startswith(f"Q{bus}_")]
    else:
        kw_columns = [f"P{bus}"]
        kvar_columns = [f"Q{bus}"]

    if not kw_columns or not kvar_columns:
        raise ValueError(f"Bus {bus} not found in case {case}.")

    # Sum phase demand when the case is unbalanced
    kw = df[kw_columns].sum(axis=1)
    kvar = df[kvar_columns].sum(axis=1)

    return df["timestamp"], kw, kvar


def plot_time_series(case, bus_number, unbalanced=UNBALANCED):
    """Plot and save active and reactive power time series for a bus."""

    timestamp, kw, kvar = read_bus_demand(case, bus_number, unbalanced)

    kw_mean = kw.mean()
    kvar_mean = kvar.mean()

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # Active power
    axes[0].plot(timestamp, kw, color=LOAD_COLOR, label="Load")
    axes[0].axhline(kw_mean, color=MEAN_COLOR, linewidth=2,
                    label=f"Mean: {kw_mean:.2f} kW")
    axes[0].set_title(f"Active Power Load - Bus {bus_number}")
    axes[0].set_ylabel("Load (kW)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Reactive power
    axes[1].plot(timestamp, kvar, color=LOAD_COLOR, label="Load")
    axes[1].axhline(kvar_mean, color=MEAN_COLOR, linewidth=2,
                    label=f"Mean: {kvar_mean:.2f} kvar")
    axes[1].set_title(f"Reactive Power Load - Bus {bus_number}")
    axes[1].set_ylabel("Load (kvar)")
    axes[1].set_xlabel("Time")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()

    # Save the figure in the corresponding case folder
    case_name = str(case) if str(case).startswith("case") else f"case{case}"
    output_path = os.path.join(OUTPUT_DIR, case_name,
                               f"bus_{bus_number:03d}_time_series.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_daily_average(case, bus_number, unbalanced=UNBALANCED):
    """Plot and save the average daily active and reactive power profiles for a bus."""

    timestamp, kw, kvar = read_bus_demand(case, bus_number, unbalanced)

    df = pd.DataFrame({"timestamp": timestamp, "kW": kw, "kvar": kvar})
    df["time"] = df["timestamp"].dt.strftime("%H:%M")

    # Calculate the average demand for each time of day
    daily_profile = df.groupby("time")[["kW", "kvar"]].mean()

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # Active power
    axes[0].plot(daily_profile.index, daily_profile["kW"],
                 marker="o", markersize=4, color=LOAD_COLOR, linewidth=2)
    axes[0].axhline(daily_profile["kW"].mean(), color=MEAN_COLOR,
                    linewidth=2, label=f"Mean: {daily_profile['kW'].mean():.2f} kW")
    axes[0].set_title(f"Average Daily Active Power Profile - Bus {bus_number}")
    axes[0].set_ylabel("Load (kW)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Reactive power
    axes[1].plot(daily_profile.index, daily_profile["kvar"],
                 marker="o", markersize=4, color=LOAD_COLOR, linewidth=2)
    axes[1].axhline(daily_profile["kvar"].mean(), color=MEAN_COLOR,
                    linewidth=2, label=f"Mean: {daily_profile['kvar'].mean():.2f} kvar")
    axes[1].set_title(f"Average Daily Reactive Power Profile - Bus {bus_number}")
    axes[1].set_ylabel("Load (kvar)")
    axes[1].set_xlabel("Time of Day")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Display fewer x-axis ticks for readability
    tick_positions = range(0, len(daily_profile), 8)
    axes[1].set_xticks(list(tick_positions))
    axes[1].tick_params(axis="x", rotation=45)

    fig.tight_layout()

    # Save the figure in the corresponding case folder
    case_name = str(case) if str(case).startswith("case") else f"case{case}"
    output_path = os.path.join(OUTPUT_DIR, case_name,
                               f"bus_{bus_number:03d}_daily_average.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_daily_average_total(case, unbalanced=UNBALANCED):
    """Plot and save the average daily total active and reactive power profiles for a case."""

    case_name = str(case) if str(case).startswith("case") else f"case{case}"
    balance_type = "unbalanced" if unbalanced else "balanced"
    file_path = os.path.join(OUTPUT_DIR, case_name, f"{balance_type}_demand.csv")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Demand file not found: {file_path}")

    df = pd.read_csv(file_path, parse_dates=["timestamp"])

    # Identify all active and reactive power columns
    kw_columns = [col for col in df.columns if col.startswith("Pbus_")]
    kvar_columns = [col for col in df.columns if col.startswith("Qbus_")]

    if not kw_columns or not kvar_columns:
        raise ValueError(f"No bus demand columns found in case {case}.")

    # Calculate total demand across all buses and phases
    total_demand = pd.DataFrame({
        "kW": df[kw_columns].sum(axis=1),
        "kvar": df[kvar_columns].sum(axis=1),
        "time": df["timestamp"].dt.strftime("%H:%M")
    })

    # Calculate the average total demand for each time of day
    daily_profile = total_demand.groupby("time")[["kW", "kvar"]].mean()

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # Active power
    axes[0].plot(daily_profile.index, daily_profile["kW"],
                 marker="o", markersize=4, color=LOAD_COLOR, linewidth=2)
    axes[0].axhline(daily_profile["kW"].mean(), color=MEAN_COLOR,
                    linewidth=2,
                    label=f"Mean: {daily_profile['kW'].mean():.2f} kW")
    axes[0].set_title(f"Average Daily Total Active Power - Case {case}")
    axes[0].set_ylabel("Total Load (kW)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Reactive power
    axes[1].plot(daily_profile.index, daily_profile["kvar"],
                 marker="o", markersize=4, color=LOAD_COLOR, linewidth=2)
    axes[1].axhline(daily_profile["kvar"].mean(), color=MEAN_COLOR,
                    linewidth=2,
                    label=f"Mean: {daily_profile['kvar'].mean():.2f} kvar")
    axes[1].set_title(f"Average Daily Total Reactive Power - Case {case}")
    axes[1].set_ylabel("Total Load (kvar)")
    axes[1].set_xlabel("Time of Day")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Display fewer x-axis ticks for readability
    tick_positions = range(0, len(daily_profile), 8)
    axes[1].set_xticks(list(tick_positions))
    axes[1].tick_params(axis="x", rotation=45)

    fig.tight_layout()

    # Save the figure in the corresponding case folder
    output_path = os.path.join(OUTPUT_DIR, case_name, "total_daily_average.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)