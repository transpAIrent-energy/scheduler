import pandas as pd
import numpy as np
import iesopt


def make_example_data():
    """Returns a full day (24 hours as 96x 15 minutes) of example data for the day-ahead scheduling model.

    The data includes:
    - Timestamps in 15-minute intervals
    - PV generation (small and large)
    - Demand (small, large, and general)
    - Day-ahead price data

    Returns:
        pd.DataFrame: DataFrame with columns `time`, `pv_s`, `pv_l`, `demand_s`, `demand_l`, `demand_g`, and `price`.
    """
    rng = np.random.default_rng(seed=42)
    return pd.DataFrame(
        {
            "time": pd.date_range(start="2025-06-02 00:00", end="2025-06-02 23:45", freq="15min", tz="Europe/Vienna"),
            "pv_s": rng.uniform(0, 330, 96),
            "pv_l": rng.uniform(0, 1110, 96),
            "demand_s": rng.uniform(50, 300, 96),
            "demand_l": rng.uniform(0, 600, 96),
            "demand_g": rng.uniform(0, 150, 96),
            "price": rng.uniform(0.02, 0.15, 96),
        }
    )


def normalize_to_eom(data: pd.DataFrame) -> pd.DataFrame:
    """Normalizes the passed DataFrame to the extend until the last 15 minute block of the month.

    This is useful to ensure that the data covers a full month, as required by the IESopt model to properly account for
    the monthly peak consumption.

    Args:
        data (pd.DataFrame): DataFrame with a 'time' column containing timestamps.

    Returns:
        pd.DataFrame: DataFrame with the 'time' column extended to the end of the month.
    """
    t0: pd.Timestamp = data["time"].iloc[0]
    end_of_month = t0.replace(day=1) + pd.DateOffset(months=1) - pd.Timedelta(minutes=15)
    data = data.loc[data["time"] <= end_of_month]

    while data["time"].iloc[-1] < end_of_month:
        tmp = data.copy()
        delta_t = data["time"].iloc[-1] - data["time"].iloc[0] + pd.Timedelta(minutes=15)
        tmp["time"] = tmp["time"] + delta_t
        data = pd.concat([data, tmp], ignore_index=True)
    return data.loc[data["time"] <= end_of_month]


def _pivot_and_clean_results(model: iesopt.Model, timestamps: pd.Series) -> pd.DataFrame:
    # Extract results.
    snapshots = model.internal.model.snapshots
    results = model.results.to_pandas()

    # Filter, prepare fullnames, and restore original times.
    results = results.loc[(results["mode"] == "primal") & ~results["snapshot"].isnull()]
    results["entry"] = results[["component", "fieldtype", "field"]].agg(".".join, axis=1)
    t_map = dict(zip([snapshots[t + 1].name for t in range(len(snapshots))], timestamps))
    results["time"] = results["snapshot"].apply(lambda t: t_map[t])

    # Pivot results to wide format.
    return results.pivot(index="time", columns="entry", values="value").loc[timestamps.iloc[0:96]]


def _str_to_cast(element: str | None) -> str | int | float | bool:
    if (element is None) or (element == ""): 
        return None
    if element.lower() == "true":
        return True
    if element.lower() == "false":
        return False
    
    try:
        return int(element)
    except ValueError:
        pass
    try:
        return float(element)
    except ValueError:
        pass
    
    return str(element)
