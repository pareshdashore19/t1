from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from t1.tools.schema.search_output import SearchResultsOutputModel


class DomainEnum(str, Enum):
    restaurant = "restaurant"
    hotel = "hotel"
    attraction = "attraction"


class FindNearestInputModel(BaseModel):
    hotels: Optional[SearchResultsOutputModel] = Field(
        default=None,
        description="Search results for hotels",
    )
    attractions: Optional[SearchResultsOutputModel] = Field(
        default=None,
        description="Search results for attractions",
    )
    restaurants: Optional[SearchResultsOutputModel] = Field(
        default=None,
        description="Search results for restaurants",
    )
    groupBy: DomainEnum = Field(
        ...,
        description="Which domain to group the results by in terms of nearest. Value will be either hotel, restaurant or attraction",
    )
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def exactly_two_fields_specified(cls, values):
        fields = [values.hotels, values.restaurants, values.attractions]
        specified_count = sum(field is not None for field in fields)
        if specified_count != 2:
            raise ValueError(
                "Exactly two fields among restaurants, attractions and hotels must be specified."
            )
        return values
