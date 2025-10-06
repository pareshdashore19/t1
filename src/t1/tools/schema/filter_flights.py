from datetime import datetime, time
from typing import Any, ClassVar, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.tools.schema.search_output import SearchResultsOutputModel


class FilterFlightsInputModel(BaseModel):
    prior_results: SearchResultsOutputModel = Field(
        ...,
        description="The results from the previous search query made by the customer",
    )

    start_airport_city: Optional[str] = Field(
        default=None,
        description="Starting airport city the user would like to fly out of",
    )
    end_airport_city: Optional[str] = Field(
        default=None,
        description="Ending airport city the user would like to fly out to.",
    )
    departure_date: Optional[List[str]] = Field(
        default=None,
        description="List of the departure dates the user would like to fly out on. Date must be a string the formats: for example - 'January 1, 2025'",
    )
    arrival_date: Optional[List[str]] = Field(
        default=None,
        description="List of the arrival dates the user would like to arrive to destination on. Date must be a string the formats: for example - 'January 1, 2025'",
    )
    departure_time: Optional[List[str]] = Field(
        default=None,
        description="List consisting of start and end departure times the user would like to arrive to destination on",
    )
    arrival_time: Optional[List[str]] = Field(
        default=None,
        description="List consisting of start and end arrival times the user would like to arrive to destination on",
    )

    flight_id: Optional[List[str]] = Field(
        default=None, description="List of flight ids the user would like to fly with."
    )
    start_airport: Optional[str] = Field(
        default=None,
        description="Starting airport the user would like to fly out of.",
    )
    end_airport: Optional[str] = Field(
        default=None,
        description="Destination airport the user would like to fly to.",
    )
    start_airport_code: Optional[str] = Field(
        default=None,
        description="Starting airport code.",
    )
    end_airport_code: Optional[str] = Field(
        default=None,
        description="List of destination airport codes.",
    )
    airline: Optional[List[str]] = Field(
        default=None,
        description="The list of possible airlines the user would like to fly with",
    )
    budget: Optional[int] = Field(
        default=None,
        description="The maximum budget the user would like to spend for a ticket",
    )
    flight_class: Optional[List[str]] = Field(
        default=None,
        description="List of the classes of the flight experience the user prefers",
    )
    num_layovers: Optional[List[int]] = Field(
        default=[0, 1],
        description="Number of layovers user prefers",
    )
    layover_1_city: Optional[List[str]] = Field(
        default=None,
        description="List containing options for the first layover city the user would prefer",
    )
    layover_2_city: Optional[List[str]] = Field(
        default=None,
        description="List containing options for the second layover city the user would prefer",
    )
    layover_1_duration_minutes: Optional[int] = Field(
        default=60, description="The duration of the first layover"
    )
    layover_2_duration_minutes: Optional[int] = Field(
        default=60, description="The duration of the second layover"
    )
    duration_minutes: Optional[int] = Field(
        default=None, description="Preferred duration of flight"
    )
    date_formats: ClassVar[List[str]] = ["%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"]

    time_formats: ClassVar[List[str]] = ["%H:%M", "%I:%M %p"]
    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "budget",
        "layover_1_duration_minutes",
        "layover_2_duration_minutes",
        "duration_minutes",
        mode="before",
    )
    @classmethod
    def enforce_int_type(cls, value: Any) -> int:
        if type(value) is int:
            return value
        if type(value) is str and value.isdigit():
            return int(value)
        raise ValueError("Value must be an integer or numeric string.")

    @field_validator("departure_date", "arrival_date", mode="before")
    @classmethod
    def normalize_dates(cls, values) -> str:
        if not isinstance(values, List):
            raise TypeError("Must be a list of strings.")

        def parse_date(date_str):
            for fmt in cls.date_formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            raise ValueError(
                f"Invalid date format. Date must be a string in one of the following formats: 'YYYY-MM-DD', 'January 1, 2025' or 'Jan 1, 2025'"
            )

        return [parse_date(d) for d in values]

    @field_validator("departure_time", "arrival_time", mode="before")
    @classmethod
    def normalize_times(cls, values) -> str:
        if not isinstance(values, List):
            raise TypeError("Must be a list of strings.")

        def normalize(t):
            if isinstance(t, time):
                return t.strftime("%H:%M:%S")
            if not isinstance(t, str):
                raise ValueError(f"Invalid time passed. {t}")
            t = t.strip()
            for fmt in cls.time_formats:
                try:
                    return datetime.strptime(t, fmt).strftime("%H:%M:%S")
                except ValueError:
                    continue
            raise ValueError("Unrecognized time format")

        return [normalize(item) for item in values]
