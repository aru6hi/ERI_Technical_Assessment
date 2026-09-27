'''Read the supplied hourly data and calculate inclusive date-range totals.'''

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path


class EnergyDataError(ValueError):
    '''Invalid request or incomplete source data.'''


@dataclass(frozen=True)
class EnergyTotal:
    start_date: date
    end_date: date
    total_kwh: Decimal


class EnergyData:
    def __init__(self, csv_path: Path):
        with Path(csv_path).open(newline="", encoding="utf-8-sig") as source:
            reader = csv.DictReader(source)
            self.readings = {}
            for row in reader:
                timestamp = datetime.fromisoformat(row["timestamp"])
                if timestamp in self.readings:
                    raise EnergyDataError(f"Duplicate reading: {timestamp}.") #Flag duplicate readings as an error
                self.readings[timestamp] = Decimal(row["energy_consumption_kwh"])

        self.first_date = min(self.readings).date()
        self.last_date = max(self.readings).date()

    def total(self, start_date: str, end_date: str) -> EnergyTotal:
        try:
            start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
            if start.isoformat() != start_date or end.isoformat() != end_date:
                raise ValueError 
        except (TypeError, ValueError) as exc:
            raise EnergyDataError("Use dates in YYYY-MM-DD format.") from exc #Flag invalid date formats as an error

        if start > end:
            raise EnergyDataError("The start date must be on or before the end date.") #Flag invalid date ranges as an error
        if start < self.first_date or end > self.last_date:
            raise EnergyDataError(f"Data is available from {self.first_date} through {self.last_date}.") #Flag out-of-range dates as an error

        total = Decimal("0")
        hour = datetime.combine(start, datetime.min.time()) #hour is set to the midnight of the start date
        stop = datetime.combine(end + timedelta(days=1), datetime.min.time()) #stop is set to the midnight of the day after the end date, making the range inclusive of the end date
        while hour < stop:
            total += self.readings[hour]
            hour += timedelta(hours=1) #Increment hour by one hour for the next iteration
        return EnergyTotal(start, end, total)
