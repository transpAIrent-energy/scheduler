from typing import List, Dict
import logging
import iesopt
import pandas as pd
from pathlib import Path
from .util import _pivot_and_clean_results


logger = logging.getLogger("uvicorn.info")


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

    # Run model
    config_file = str((Path(config_path) / "config.iesopt.yaml").resolve())
    model = iesopt.run(
        config_file,
        config={"optimization.snapshots.count": len(data)},
        parameters=parameters,
        virtual_files=dict(data=data),
    )

    # Extract model internal information and results.
    battery_e = model.internal.input.parameters["battery_e"]
    results = _pivot_and_clean_results(model, data["time"])

    # Check feasibility & soft constraints.
    if results["bromberg.battery_storage.var.softmin"].max() > 1e-3:
        logger.warning("Day-ahead schedule model: Battery SoC softmin constraint was violated!")

    if results.filter(like=".feasibility_").filter(like=".exp.value").max().max() > 1e-3:
        logger.warning("Day-ahead schedule model: Some feasibility constraints were violated!")

    # Extract selected results (copying to make sure Python GC picks up on the "free" afterwards).
    results = pd.DataFrame(
        {
            "schedule_bromberg_kW": results["metering_bromberg.var.flow"],
            "schedule_brunn_kW": results["metering_brunn.var.flow"],
            "schedule_kirchschlag_kW": results["metering_kirchschlag.var.flow"],
            "battery_setpoint_kW": (
                results["bromberg.battery_discharging.exp.out_electricity"]
                - results["bromberg.battery_charging.exp.in_electricity"]
            ),
            "battery_soc": results["bromberg.battery_storage.var.state"] / battery_e,
        }
    ).copy()

    # Free model resources.
    del model
    model = None

    # Return selected results.
    return results
