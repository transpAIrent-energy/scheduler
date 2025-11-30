#
# AIT Scheduler Web Service
#
# based on FastAPI
# Environment setup: pip3 install fastapi[standard] iesopt pandas
# Run dev server: fastapi dev scheduler-webservice.py --port 8000
#

import logging
from typing import List, Dict
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
from pathlib import Path
from src.util import normalize_to_eom
from src.scheduler import get_day_ahead_schedule


class ScheduleInput(BaseModel):
    start_time: datetime  # Start time of the scheduling period
    data: List[Dict[str, float]]  # Each data point is a dict of float values
    parameters: Dict[str, float]  # Generic parameters as key-value pairs


class ScheduleOutput(BaseModel):
    data: List[Dict[str, float]] | None = None
    error: str | None = None


app = FastAPI()
logger = logging.getLogger('uvicorn.info')


@app.post("/schedule", response_model=ScheduleOutput)
async def schedule(input_data: ScheduleInput):
    try:
        config_path = str((Path(".") / "opt").resolve())
        data = pd.DataFrame(input_data.data)
        parameters = input_data.parameters
        start_time = input_data.start_time
        logger.info(f"Received scheduling request with {len(data)} data points starting at {start_time.isoformat()} "
                    f"and {len(parameters)} parameters")
        data = normalize_to_eom(data, start_time)
        logger.info(f"Normalized data from {start_time.isoformat()} to end of month --> {len(data)} datapoints")
        result_data = get_day_ahead_schedule(data, parameters, config_path)
        logger.info(f"Scheduling completed, returning {len(result_data)} result data points")
        result_data = result_data.to_dict(orient="records")
        return ScheduleOutput(data=result_data)
    except Exception as e:
        logger.error(f"Error running AIT scheduler: {e}", exc_info=e)
        return ScheduleOutput(error=str(e))


@app.get("/healthcheck")
async def healthcheck():
    return "OK"
