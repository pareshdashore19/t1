from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from t1.tools.schema.search_output import SearchResultsOutputModel


class FilterRestaurantsInputModel(BaseModel):
    prior_results: SearchResultsOutputModel = Field(
        ...,
        description="The results from the previous search query made by the customer",
    )
    city: Optional[str] = Field(
        default=None,
        description="City the user would like to look for a restaurant at.",
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of neighborhoods the user would look to look for a restaurant at.",
    )
    rating: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum ratings the user is willing to consider for a restaurant.",
    )
    restaurant_name: Optional[List[str]] = Field(
        default=None,
        description="List of restaurant names the user would like to look at",
    )

    budget: Optional[int] = Field(
        default=None,
        description="Maximum budget of the user for a restaurant per person",
    )
    has_nut_allergy_options: Optional[bool] = Field(
        default=None,
        description="Whether or not user wants a restaurant with nut allergy options True or False.",
    )
    has_dairy_allergy_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a restaurant with dairy allergy options. True or False.",
    )
    has_shell_fish_allergy_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a restaurant with shell fish allergy options. True or False.",
    )
    has_tomato_allergy_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a restaurant with tomato allergy options. True or False.",
    )
    has_gluten_free_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a restaurant with gluten free options. True or False.",
    )
    has_vegetarian_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a restaurant with vegetarian options True or False.",
    )
    has_vegan_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a restaurant with vegan options. True or False.",
    )
    has_kosher_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a restaurant with Kosher options True or False.",
    )
    has_halal_options: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a restaurant with Halal options. True or False.",
    )
    cuisine: Optional[List[str]] = Field(
        default=None,
        description="List of cuisines the user would like the restaurant to have.",
    )
    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "budget",
        mode="before",
    )
    @classmethod
    def enforce_int_type(cls, value: Any) -> int:
        if type(value) is int:
            return value
        if type(value) is str and value.isdigit():
            return int(value)
        raise ValueError("Value must be an integer or numeric string.")

    @field_validator("rating", mode="before")
    @classmethod
    def enforce_float_range(cls, value: Any) -> List[float]:
        if not type(value) is list:
            raise ValueError(f"ratings must be a list. got {type(value)}")
        if len(value) != 2:
            raise ValueError("ratings must contain exactly two items.")
        result = []
        for v in value:
            try:
                result.append(float(v))
            except (ValueError, TypeError):
                raise ValueError(
                    "Each item in the list must be either an integer or a float."
                )
        return result
