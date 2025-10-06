from datetime import datetime
from typing import ClassVar, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AdjustDateInputModel(BaseModel):
    date: str = Field(
        default=None,
        description="Date provided as reference point. Must be in YYYY-MM-DD or MM DD, YYYY",
    )
    delta_days: int = Field(
        default=None,
        description="Number of days to adjust date by. Can be positive or negative.",
    )

    formats: ClassVar[List[str]] = ["%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"]
    model_config = ConfigDict(extra="forbid")

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, values) -> str:
        for fmt in cls.formats:
            try:
                datetime.strptime(values, fmt)
                return values
            except ValueError:
                continue
        raise ValueError(
            "date must be a string in one of the following formats: 'YYYY-MM-DD', 'January 1, 2025' or 'Jan 1, 2025'"
        )
