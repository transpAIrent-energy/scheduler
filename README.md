# transpAIrent.energy: Scheduler

A day-ahead operational scheduler for the transpAIrent.energy project.

ToDo: updated docs to new FastAPI Webservice interface

## Setup

Clone this repository, e.g., by doing:

```bash
git clone https://github.com/transpAIrent-energy/scheduler.git
```

Then, navigate to the project directory and run the following command to set up the virtual environment:

```bash
uv sync
```

> [!TIP]
> If possible it's best to trigger the one-time Julia setup (environment creation, package installation,
> precompilation, etc.) manually once since that step can take a few minutes. You can do this by launching Python in
> the virtual environment (e.g., by doing `uv run python`) and then importing the `iesopt` package once (by executing
> `import iesopt`). This will ensure that the environment is created and all packages are installed and precompiled,
> which is then re-used when using the same environment.

## Parameters (.env)

Add a `.env` file in the project root directory with the following parameters:

```env
# ------------------ BATTERY ------------------

battery_p=1234.5           # [kW] Rated power of the battery
battery_e=1234.5           # [kWh] Energy capacity of the battery
battery_eta=0.123          # [1] Total roundtrip efficiency of the battery
battery_loss=0.123         # [1] Self-discharge rate of the battery, per hour
battery_soc_min=0.0        # [1] Minimum state of charge of the battery
battery_soc_max=1.0        # [1] Maximum state of charge of the battery
battery_vom=0.123          # [EUR/kWh] Costs associated with charging+discharging the battery by 1 kWh

# --------------- GRID TARIFFS ----------------

grid_p_max_consume=1234.5  # [kW] Maximum rated power of the grid connection (consumption)
grid_p_max_feedin=1234.5   # [kW] Maximum rated power of the grid connection (feed-in)
grid_cost_e_consume=0.123  # [EUR/kWh] Energy cost of consuming electricity from the grid
grid_cost_e_feedin=0.123   # [EUR/kWh] Energy cost of feeding electricity into the grid
grid_cost_p_consume=0.123  # [EUR/kW] Power cost of the grid connection, for the current month (so divided by 12!)
```

## Model description

### Results

Results are - as most values - given in `kW` for setpoints, etc., and unitless (0-1) for the state of charge (SoC). The
SoC is given as a fraction of the battery's total energy capacity (so `0.9` refers to the upper bound of the allowed
range of operation if `battery_soc_max` is set to `0.9`).

This is especially important for schedule related results, where the 15-minute intervals implicate that results (in
terms of power) are not (numerically) equal to the corresponding energy values (in kWh) for the same time period.

### Storage levels

The scheduler currently starts at `00:00` and runs until the end of the passed data window, forcing the storage to have
at least the initial state of charge at the end of the scheduling period (ending with more stored energy is allowed).

### Storage & self-consumption

The storage is currently configured to not allow discharging to sell on the day-ahead market - assuming that forecasts
are not accurate enough to ensure large enough spreads (when accounting for grid costs, degradation, etc.) to allow
trading spreads across the day. This is done by only allowing it to discharge to cover the local demand. Charging is
allowed from either the PV or the grid.

## Example usage

Put the following into `example.py`:

```python
from src.util import make_example_data, normalize_to_eom
from src.scheduler import get_day_ahead_schedule


data = make_example_data()
data = normalize_to_eom(data)

schedule = get_day_ahead_schedule(data, battery_soc_t0=0.5, grid_p_peak_consume=100)

print(schedule.head())
```

Then run:

```bash
uv run example.py
```

which should print the first few rows of the resulting schedule, similar to:

```console
                            schedule  battery_setpoint  battery_soc
time                                                               
2025-06-02 00:00:00+02:00 -205.62232          0.000000     0.500000
2025-06-02 00:15:00+02:00  123.41780        101.236946     0.499925
2025-06-02 00:30:00+02:00  123.41780        158.318582     0.495171
2025-06-02 00:45:00+02:00 -990.00000        -39.164461     0.487780
2025-06-02 01:00:00+02:00  123.41780       -390.498286     0.489336
```
