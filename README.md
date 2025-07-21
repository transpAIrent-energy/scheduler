# transpAIrent.energy: Scheduler

A day-ahead operational scheduler for the transpAIrent.energy project.

## Setup

Clone this repository, e.g., by doing:

```bash
git clone https://github.com/transpAIrent-energy/scheduler.git
```

Then, navigate to the project directory and run the following command to set up the virtual environment:

```bash
uv sync
```

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
