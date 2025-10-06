from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SearchAttractionsInputModel(BaseModel):
    city: Optional[str] = Field(
        default=None,
        description="City the user would like to look for an attraction at.",
    )
    state: Optional[str] = Field(
        default=None,
        description="State the user would like to look for an attraction at.",
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of neighborhoods the user would like to look for an attraction at.",
    )
    type: Optional[List[str]] = Field(
        default=None,
        description="List of attraction types the user would be interested in ",
    )
    attraction_name: Optional[List[str]] = Field(
        default=None,
        description="List of attraction names the user would like to look at",
    )
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def exactly_two_fields_specified(cls, values):
        fields = [values.city, values.state]
        specified_count = sum(field is not None for field in fields)
        if specified_count < 1:
            raise ValueError(
                "At least one of city or state of the attraction must be specified."
            )
        return values
