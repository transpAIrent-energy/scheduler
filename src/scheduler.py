import iesopt
import pandas as pd
from pathlib import Path
from dotenv import dotenv_values

from .util import _pivot_and_clean_results, _str_to_cast


def get_day_ahead_schedule(data: pd.DataFrame, *, battery_soc_t0: float, grid_p_peak_consume: float, path: str = "./opt") -> pd.DataFrame:
    """
    Calculates the day-ahead schedule based on the provided data.

    This function runs the IESopt model with the provided data and parameters to generate a day-ahead schedule.
    It expects the data to start at midnight (00:00:00) and contain at least 96 entries (representing a full day in
    15-minute intervals). All input values are given in `kW` except for `price` (EUR/kWh) and `battery_soc_t0` (0-1).

    Args:
        data (pd.DataFrame): DataFrame containing the day-ahead data with columns `time`, `pv_s`, `pv_l`, `demand_s`,
                             `demand_l`, `demand_g`, and `price`.
        battery_soc_t0 (float): Initial state of charge of the battery at the start of the day.
        grid_p_peak_consume (float): Already realized (previous) peak consumption from the grid.

    Returns:
        pd.DataFrame: DataFrame containing the day-ahead schedule with columns `schedule` (given in kW, positive values
                      correspond to consumption, negative values to feed-in), `battery_setpoint` (kW, positive values
                      correspond to discharging, negative values to charging), and `battery_soc` (0-1, scaled to the
                      battery's total - not usable - capacity).
    """
    t0 = data["time"].iloc[0]
    if t0.hour != 0 or t0.minute != 0 or t0.second != 0:
        raise ValueError("Data must start at midnight (00:00:00) of the day (-ahead) to be scheduled.")
    if len(data) < 96:
        raise ValueError("Data must contain at least 96 entries (a full day in 15-minute intervals).")

    # TODO: Check for proper 15-minute intervals.

    # Prepare model (and parameter) paths.
    path_config = str((Path(path) / "config.iesopt.yaml").resolve())
    path_dotenv = str((Path(path) / ".env").resolve())

    # Prepare parameters from the `.env` file and given arguments.
    parameters = {k: _str_to_cast(v) for (k, v) in dotenv_values(path_dotenv).items()}
    parameters["battery_soc_t0"] = battery_soc_t0
    parameters["grid_p_peak_consume"] = grid_p_peak_consume

    # Run IESopt model.
    model = iesopt.run(
        path_config,
        config={"optimization.snapshots.count": len(data)},
        parameters=parameters,
        virtual_files=dict(data=data),
    )

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
