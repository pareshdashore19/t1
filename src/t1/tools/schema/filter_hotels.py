from datetime import datetime
from typing import Any, ClassVar, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from t1.tools.schema.search_output import SearchResultsOutputModel


class FilterHotelsInputModel(BaseModel):
    prior_results: SearchResultsOutputModel = Field(
        ...,
        description="The results from the previous search query made by the customer",
    )
    checkin_date: Optional[List[str]] = Field(
        default=None,
        description="List of the check-in dates the user would like to check-in to a hotel. Date must be a string the formats: for example - 'January 1, 2025' ",
    )
    checkout_date: Optional[List[str]] = Field(
        default=None,
        description="List of the check out dates the user would like to check out of a hotel. Date must be a string the formats: for example - 'January 1, 2025' ",
    )
    num_rooms: Optional[int] = Field(
        default=None,
        description="Number of rooms the user would like to book at hotel.",
    )
    num_people: Optional[int] = Field(
        default=None,
        description="Number of people the user would like to book at hotel.",
    )
    neighborhood: Optional[List[str]] = Field(
        default=None,
        description="List of neighborhoods the user would look to look for a hotel at.",
    )
    rating: Optional[List[float]] = Field(
        default=None,
        description="Consists of the minimum and maximum ratings the user is willing to consider for a hotel",
    )
    stars: Optional[List[int]] = Field(
        default=None,
        description="Consists of the minimum and maximum star values of the hotel the user is interested in.",
    )
    hotel_name: Optional[List[str]] = Field(
        default=None,
        description="List of hotel names the user would like to look at",
    )

    budget: Optional[int] = Field(
        default=None,
        description="Maximum budget of the user for booking a hotel per night",
    )
    gym_present: Optional[bool] = Field(
        default=None,
        description="Whether or not user wants a gym present in the hotel. True or False.",
    )
    pool_present: Optional[bool] = Field(
        default=None,
        description="Whether or not user wants a pool present in the hotel. True or False.",
    )
    breakfast_included: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel that includes breakfast. True or False.",
    )
    smoking_allowed: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel that allows smoking. True or False.",
    )
    air_conditioning_present: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel that includes air conditioning. True or False.",
    )
    heating_present: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel that includes heating. True or False.",
    )
    free_wifi_included: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel with free wifi. True or False.",
    )
    airport_shuttle_present: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has an airport shuttle. True or False.",
    )
    is_pet_friendly: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which is pet friendly and allows a pet. True or False.",
    )
    has_spa_services: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has spa services. True or False.",
    )
    has_room_service: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has room service. True or False.",
    )
    has_beach_access: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has access to a beach. True or False.",
    )
    has_business_center: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has a business center. True or False.",
    )
    has_fitness_class: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has a fitness class. True or False.",
    )
    has_laundry_service: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has a laundry service. True or False.",
    )
    has_valet_parking: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has valet parking. True or False.",
    )
    has_balcony: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel has a balcony. True or False.",
    )
    has_rooftop_bar: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has a rooftop bar. True or False.",
    )
    has_inroom_kitchen: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has an in-room kitchen. True or False.",
    )
    has_kids_club: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has a kids club. True or False.",
    )
    has_meeting_rooms: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has meeting rooms. True or False.",
    )
    has_electric_vehicle_charging: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has electric vehicle charging. True or False.",
    )
    has_hot_tub: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has a hot tub. True or False.",
    )
    has_sauna: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has a sauna. True or False.",
    )
    has_free_parking: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has free parking. True or False.",
    )
    is_wheelchair_accessible: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which is wheelchair accessible. True or False.",
    )
    has_skiing_lodging: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which is has skiing lodging. True or False.",
    )
    has_ocean_view_rooms_present: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has rooms with a view of the ocean present. True or False",
    )
    has_city_view_rooms_present: Optional[bool] = Field(
        default=None,
        description="Whether or not the user wants a hotel which has rooms present with a view of the city. True or False.",
    )
    formats: ClassVar[List[str]] = ["%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"]
    model_config = ConfigDict(extra="forbid")

    @field_validator("checkin_date", "checkout_date", mode="before")
    @classmethod
    def normalize_dates(cls, values) -> str:
        if not isinstance(values, List):
            raise TypeError("Must be a list of strings.")

        def parse_date(date_str):
            for fmt in cls.formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            raise ValueError(
                f"Invalid date format. Date must be a string in one of the following formats: 'YYYY-MM-DD', 'January 1, 2025' or 'Jan 1, 2025'"
            )

        return [parse_date(d) for d in values]
