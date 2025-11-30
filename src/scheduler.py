from typing import List, Dict
import logging
import iesopt
import pandas as pd
from pathlib import Path
from dotenv import dotenv_values
from .util import _pivot_and_clean_results, _str_to_cast


def get_day_ahead_schedule(data: pd.DataFrame, parameters: Dict[str, float], config_path: str) -> pd.DataFrame:
    """
    Calculates the day-ahead schedule based on the provided data.
    Runs the IESopt model with the provided data and parameters to generate a day-ahead schedule.
    It expects the data to contain at least 96 entries (representing a full day in 15-minute intervals).
    All input values are given in `kW` except for `price` (EUR/kWh) and `battery_soc_t0` (0-1).
    @param data: DataFrame containing the input data for the model.
    @param parameters: Dictionary containing model parameters
    @param configpath: Path to the IESopt model configuration files.
    @return: DataFrame containing the day-ahead schedule.
             Columns `schedule` (given in kW, positive values correspond to consumption, negative values to feed-in),
                     `battery_setpoint` (kW, positive values correspond to discharging, negative values to charging),
                     `battery_soc` (0-1, scaled to the battery's total - not usable - capacity).
    """
    if len(data) < 96:
        raise ValueError("Data must contain at least 96 entries (a full day in 15-minute intervals).")

    # TODO: Check for proper 15-minute intervals.

    # Run model
    config_file = str((Path(config_path) / "config.iesopt.yaml").resolve())
    model = iesopt.run(config_file, config={"optimization.snapshots.count": len(data)}, parameters=parameters,
                       virtual_files=dict(data=data))

    # Extract model internal information and results.
    battery_e = model.internal.input.parameters["battery_e"]
    results = _pivot_and_clean_results(model, data["time"])

    # Return selected results.
    model = None
    return pd.DataFrame(
        {
            "schedule": results["market_da_buy.exp.value"] - results["market_da_sell.exp.value"],
            "battery_setpoint": (
                    results["battery_discharging.exp.out_electricity"] - results["battery_charging.exp.in_electricity"]
            ),
            "battery_soc": results["battery_storage.var.state"] / battery_e,
        }
    )
