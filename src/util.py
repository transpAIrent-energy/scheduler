import logging
import math
from datetime import datetime
import pandas as pd
import iesopt

logger = logging.getLogger('uvicorn.info')


def normalize_to_eom(data: pd.DataFrame, start_time: datetime) -> pd.DataFrame:
    """Normalizes the passed DataFrame to the extend until the last 15 minute block of the month.
    This is useful to ensure that the data covers a full month, as required by the IESopt model to properly account for
    the monthly peak consumption.
    @param data: DataFrame
    @param start_time: start timestamp of the data frame
    @return: DataFrame with data extended to the end of the month, and a time column added.
    """
    # Compute end of month (last 15-min block)
    step = pd.Timedelta(minutes=15)
    month_start = start_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + pd.DateOffset(months=1)
    end_of_month = month_start - step
    logger.info(f"Normalizing: start_time={start_time}, end_of_month={end_of_month}")
    # Number of samples needed from start_time to end_of_month (inclusive)
    n_required = int((end_of_month - start_time) / step) + 1
    # Workaround: if we are near the end of the month, we need to have at least 2 days
    if n_required < 192:
        n_required = 192
    n_available = len(data)
    logger.info(f"Normalizing data: available={n_available}, required={n_required}")
    if n_available >= n_required:
        result = data.iloc[:n_required].reset_index(drop=True)
    else:
        repeats = math.ceil(n_required / n_available)
        result = pd.concat([data] * repeats, ignore_index=True).iloc[:n_required]
    # Add time column
    time_index = pd.date_range(start=start_time, periods=n_required, freq="15min")
    result = result.copy()
    result.insert(0, "time", time_index)
    return result


def _pivot_and_clean_results(model: iesopt.Model, timestamps: pd.Series) -> pd.DataFrame:
    snapshots = model.internal.model.snapshots
    results = model.results.to_pandas()
    # Filter, prepare fullnames and restore timestamps.
    results = results.loc[(results["mode"] == "primal") & ~results["snapshot"].isnull()]
    results["entry"] = results[["component", "fieldtype", "field"]].agg(".".join, axis=1)
    t_map = dict(zip([snapshots[t + 1].name for t in range(len(snapshots))], timestamps))
    results["time"] = results["snapshot"].apply(lambda t: t_map[t])
    # Pivot results to wide format.
    final_result = results.pivot(index="time", columns="entry", values="value").loc[timestamps.iloc[0:]]
    return final_result


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
