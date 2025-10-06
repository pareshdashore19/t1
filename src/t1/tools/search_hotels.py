import os
from datetime import datetime

import pandas as pd

from t1.tools.schema.search_hotels import SearchHotelsInputModel
from t1.tools.schema.search_output import SearchResultsOutputModel

all_hotels_df = pd.read_csv(os.getenv("ALL_HOTELS"))
all_hotels_df["start_date_available"] = pd.to_datetime(
    all_hotels_df["start_date_available"], format="%Y-%m-%d"
).dt.date
all_hotels_df["end_date_available"] = pd.to_datetime(
    all_hotels_df["end_date_available"], format="%Y-%m-%d"
).dt.date


def summarize_query(search_input_filtered):
    hotel_amenities = [
        "gym_present",
        "breakfast_included",
        "pool_present",
        "smoking_allowed",
        "air_conditioning_present",
        "heating_present",
        "free_wifi_included",
        "airport_shuttle_present",
        "airport_shuttle_present",
        "is_pet_friendly",
        "has_spa_services",
        "has_room_service",
        "has_beach_access",
        "has_business_center",
        "has_fitness_class",
        "has_laundry_service",
        "has_valet_parking",
        "has_balcony",
        "has_rooftop_bar",
        "has_inroom_kitchen",
        "has_kids_club",
        "has_meeting_rooms",
        "has_electric_vehicle_charging",
        "has_hot_tub",
        "has_sauna",
        "has_free_parking",
        "is_wheelchair_accessible",
        "has_skiing_lodging",
        "has_ocean_view_rooms_present",
        "has_city_view_rooms_present",
    ]

    result = []
    hotel_city = search_input_filtered["city"]
    checkin_date = ", ".join(search_input_filtered["checkin_date"])
    checkout_date = ", ".join(search_input_filtered["checkout_date"])
    result.append(
        "Hotel search results in {} from check-in date(s) [{}] to check-out date(s) [{}].".format(
            hotel_city,
            checkin_date,
            checkout_date,
        )
    )

    if "num_rooms" in search_input_filtered:
        result.append(
            "Number of room(s): {},".format(search_input_filtered["num_rooms"])
        )

    if "num_people" in search_input_filtered:
        result.append(
            "Number of traveler(s): {},".format(search_input_filtered["num_people"])
        )

    if "stars" in search_input_filtered:
        res = [str(s) for s in search_input_filtered["stars"]]
        result.append("stars range: [{}],".format(", ".join(res)))

    if "rating" in search_input_filtered:
        res = [str(s) for s in search_input_filtered["rating"]]
        result.append("rating range: [{}],".format(", ".join(res)))

    if "neighborhood" in search_input_filtered:
        result.append(
            "neighborhood(s): [{}],".format(
                ", ".join(search_input_filtered["neighborhood"])
            )
        )

    if "hotel_name" in search_input_filtered:
        result.append(
            "hotel name(s): [{}],".format(
                ", ".join(search_input_filtered["hotel_name"])
            )
        )

    if "budget" in search_input_filtered:
        result.append("budget: ${},".format(search_input_filtered["budget"]))

    for each_amenity in hotel_amenities:
        if each_amenity in search_input_filtered:
            if search_input_filtered[each_amenity]:
                result.append(each_amenity + ",")

    final_result = " ".join(result)
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."

    return final_result


def search_hotels(**kwargs: SearchHotelsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for hotels based on several criteria such as city, whether amenities are present such as breakfast, gym, pool

    Examples:
    >>> # Usage Example:
    search_hotels(city="Key West",checkin_date=["2025-08-03", "2025-08-04"], checkout_date=["2025-08-11"], num_rooms=1)

    >>> # Usage Example:
    search_hotels(city="Los Angeles",checkin_date=["2025-09-01"],checkout_date=["2025-09-03", "2025-09-04"],num_rooms=2, rating=3, stars=[2,3,4])

    >>> # Usage Example:
    search_hotels(city="San Francisco",checkin_date=["2026-01-02"],checkout_date=["2026-01-05"], breakfast_included=True, smoking_allowed=False)

    >>> # Usage Example:
    search_hotels(city="San Jose",checkin_date=["2025-10-01", "2025-10-02"],checkout_date=["2025-10-08", "2025-10-09", "2025-10-10"], budget=350, breakfast_included=True, smoking_allowed=False, heating_present=True)

    >>> # Usage Example:
    search_hotels(city="Phoenix",checkin_date=["2025-10-21"],checkout_date=["2025-10-31"], budget=1000, breakfast_included=True, "smoking_allowed"=False, air_conditioning_present=True ,heating_present=True)

    Returns:
        SearchHotelsOutputModel: Output object which contains the resulting hotels as well as the summary.
    """
    search_input = SearchHotelsInputModel.model_validate(kwargs)
    search_input_filtered = {
        k: v for k, v in search_input.dict().items() if v is not None
    }
    mask = pd.Series(True, index=all_hotels_df.index)
    for col, search_query_parameters in search_input_filtered.items():
        if type(search_query_parameters) is list:
            if col == "checkin_date" or col == "checkout_date":
                date_objects = [
                    datetime.strptime(t, "%Y-%m-%d").date()
                    for t in search_query_parameters
                ]
                hotel_date_mask = pd.concat(
                    [
                        (all_hotels_df["start_date_available"] <= d)
                        & (d <= all_hotels_df["end_date_available"])
                        for d in date_objects
                    ],
                    axis=1,
                ).any(axis=1)
                mask &= hotel_date_mask
            elif col == "rating" or col == "stars":
                mask &= (all_hotels_df[col] >= search_query_parameters[0]) & (
                    all_hotels_df[col] <= search_query_parameters[1]
                )
            else:
                mask &= all_hotels_df[col].isin(search_query_parameters)

        elif type(search_query_parameters) is int:
            if col == "budget":
                mask &= all_hotels_df["price_per_night"] <= search_query_parameters
            elif col == "num_people":
                mask &= all_hotels_df["max_occupancy"] >= search_query_parameters
            else:
                mask &= all_hotels_df["num_rooms_available"] >= search_query_parameters
        elif (
            type(search_query_parameters) is str
            or type(search_query_parameters) is bool
        ):
            mask &= all_hotels_df[col] == search_query_parameters
    resulting_hotels = (all_hotels_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)

    if len(resulting_hotels) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_hotels,
            query_summary=f"{summarized_query}",
        )
    result = SearchResultsOutputModel(
        search_results=resulting_hotels,
        query_summary=f"{summarized_query}\nThere are {len(resulting_hotels)} hotel(s) that matched this query!",
    )
    return result
