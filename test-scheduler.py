import pandas as pd
import numpy as np
from pathlib import Path
from src.util import normalize_to_eom
from src.scheduler import get_day_ahead_schedule


# # ------------------ BATTERY ------------------
#
# battery_p=1200.0               # [kW] Rated power of the battery
# battery_e=5702.0               # [kWh] Energy capacity of the battery
# battery_eta=0.90               # [1] Total roundtrip efficiency of the battery
# battery_loss=0.0006            # [1] Self-discharge rate of the battery, per hour
# battery_soc_min=0.00           # [1] Minimum state of charge of the battery
# battery_soc_max=0.90           # [1] Maximum state of charge of the battery
# battery_vom=0.065              # [EUR/kWh] Costs associated with charging+discharging the battery by 1 kWh
#
# # --------------- GRID TARIFFS ----------------
#
# grid_p_max_consume=1121.0      # [kW] Maximum rated power of the grid connection (consumption)
# grid_p_max_feedin=990.0        # [kW] Maximum rated power of the grid connection (feed-in)
# grid_cost_e_consume=0.03324    # [EUR/kWh] Energy cost of consuming electricity from the grid
# grid_cost_e_feedin=0.0         # [EUR/kWh] Energy cost of feeding electricity into the grid
# grid_cost_p_consume=6.19633    # [EUR/kW] Power cost of the grid connection, for the current month (so divided by 12!)
#
# # ---------- DATA SOURCES / NOTES -------------
#
# # grid_cost_p_consume: based on `74.3560 EUR/kW/a`, divided by 12 months
# # grid_cost_e_feedin:  0.0, since grid connection less than 5 MW
# # grid tariffs based on `AT_NOE_NE5_2025`
# # grid tariffs do not include the final 20% VAT


def make_example_data(count: int) -> pd.DataFrame:
    """Returns `count` times 15 minutes of example data for the day-ahead scheduling model.

    The data includes:
    - Timestamps in 15-minute intervals
    - PV generation (small and large)
    - Demand (small, large, and other sites)
    - Day-ahead price data

    Returns:
        pd.DataFrame: DataFrame with columns `time`, `pv_s`, `pv_l`, `demand_bromberg_s`, `demand_bromberg_l`,
                      `demand_brunn`, `demand_kirchschlag`, and `price`.
    """
    rng = np.random.default_rng(seed=42)
    return pd.DataFrame(
        {
            "pv_s": rng.uniform(0, 330, count),
            "pv_l": rng.uniform(0, 1110, count),
            "demand_bromberg_s": rng.uniform(50, 300, count),
            "demand_bromberg_l": rng.uniform(0, 600, count),
            "demand_brunn": rng.uniform(0, 1800, count),
            "demand_kirchschlag": rng.uniform(0, 450, count),
            "price": rng.uniform(0.02, 0.15, count),
        }
    )


if __name__ == "__main__":
    start_time = pd.Timestamp("2024-06-15 00:00:00")
    data = make_example_data(96)
    parameters = {
        # initial conditions
        "battery_soc_t0": 0.5,
        "bromberg_grid_p_peak_consume": 0,
        "brunn_grid_p_peak_consume": 0,
        "kirchschlag_grid_p_peak_consume": 0,
        # general parameters
        "self_consumption_penalty": 0.005,
        "battery_soc_softmin": 0.20,
        "battery_soc_softmin_penalty": 0.05,
        # battery parameters
        "battery_p": 1200.0,
        "battery_e": 5702.0,
        "battery_eta": 0.90,
        "battery_loss": 0.0006,
        "battery_soc_min": 0.00,
        "battery_soc_max": 0.90,
        "battery_vom": 0.065,
        # grid tariff parameters (Bromberg)
        "bromberg_grid_p_max_consume": 1121.0,
        "bromberg_grid_p_max_feedin": 990.0,
        "bromberg_grid_cost_e_consume": 0.03324,
        "bromberg_grid_cost_e_feedin": 0.0,
        "bromberg_grid_cost_p_consume": 6.19633,
        # grid tariff parameters (Brunn)
        "brunn_grid_p_max_consume": 1800.0,          # TODO: check
        "brunn_grid_cost_e_consume": 0.03324,        # TODO: change
        "brunn_grid_cost_p_consume": 6.19633,        # TODO: change
        # grid tariff parameters (Kirchschlag)
        "kirchschlag_grid_p_max_consume": 450.0,     # TODO: check
        "kirchschlag_grid_cost_e_consume": 0.03324,  # TODO: change
        "kirchschlag_grid_cost_p_consume": 6.19633,  # TODO: change
    }
    config_path = str((Path(".") / "opt").resolve())
    data = normalize_to_eom(data, start_time)
    result_data = get_day_ahead_schedule(data, parameters, config_path)
    print(result_data)
