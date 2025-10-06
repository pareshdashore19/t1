import os
import re
from datetime import datetime

import pandas as pd

from src.tools.schema.filter_hotels import FilterHotelsInputModel
from src.tools.schema.search_output import SearchResultsOutputModel


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
        " has_kids_club",
        "has_meeting_rooms",
        "has_electric_vehicle_charging",
        "has_hot_tub",
        "has_sauna",
        "has_free_parking",
        "is_wheelchair_accessible",
        "has_skiing_lodging",
        "has_ocean_view_rooms_present",
        " has_city_view_rooms_present",
    ]
    result = []
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


def filter_hotels(**kwargs: FilterHotelsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for hotels based on several criteria such as city, whether amenities are present such as breakfast, gym, pool

    Examples:
    >>> # Usage Example:
    filter_hotels(prior_results=hotel_results, gym_present=True)

    >>> # Usage Example:
    filter_hotels(prior_results=hotel_results,checkin_date=["2025-09-01"],checkout_date=["2025-09-03", "2025-09-04"],rating=3, stars=[2,3,4])

    >>> # Usage Example:
    filter_hotels(prior_results=hotel_results, breakfast_included="Yes", smoking_allowed=False)

    >>> # Usage Example:
    filter_hotels(prior_results=hotel_results,checkin_date=["2025-10-01"],checkout_date=["2025-10-08"], budget=350, breakfast_included=True, smoking_allowed=False, heating_present=True)

    >>> # Usage Example:
    filter_hotels(prior_results=hotel_results,checkin_date=["2025-10-21"],checkout_date=["2025-10-31"], budget=1000, breakfast_included=True, "smoking_allowed"=False, air_conditioning_present=True ,heating_present=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting hotels as well as the summary.
    """
    search_input = FilterHotelsInputModel.model_validate(kwargs)
    search_input_filtered = {
        k: v for k, v in search_input.dict().items() if v is not None
    }
    all_hotels_df = pd.DataFrame(
        search_input_filtered["prior_results"]["search_results"]
    )
    if len(all_hotels_df) == 0:
        summarized_query = summarize_query(search_input_filtered)
        prior_summary = search_input_filtered["prior_results"]["query_summary"]
        prior_summary = re.sub(
            r"There are.*?that matched this query!\.?$", "", prior_summary.strip()
        )
        complete_query = (
            f"{prior_summary}\nAdditionally filtering for {summarized_query}"
        )

        return SearchResultsOutputModel(
            search_results=[],
            query_summary=f"{complete_query}\n",
        )
    mask = pd.Series(True, index=all_hotels_df.index)
    all_hotel_columns = list(all_hotels_df.columns)
    for col, search_query_parameters in search_input_filtered.items():
        if col == "prior_results":
            continue
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
            elif col == "rating":
                if "rating_hotels" in all_hotel_columns:
                    mask &= all_hotels_df["rating_hotels"].isin(search_query_parameters)
                else:
                    mask &= (all_hotels_df[col] >= search_query_parameters[0]) & (
                        all_hotels_df[col] <= search_query_parameters[1]
                    )

            elif col == "stars":
                if "stars_hotels" in all_hotel_columns:
                    mask &= all_hotels_df["stars_hotels"].isin(search_query_parameters)
                else:
                    mask &= (all_hotels_df[col] >= search_query_parameters[0]) & (
                        all_hotels_df[col] <= search_query_parameters[1]
                    )
            elif col == "neighborhood" and "neighborhood_hotels" in all_hotel_columns:
                mask &= all_hotels_df["neighborhood_hotels"].isin(
                    search_query_parameters
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

    prior_summary = search_input_filtered["prior_results"]["query_summary"]
    prior_summary = re.sub(
        r"There are.*?that matched this query!\.?$", "", prior_summary.strip()
    )
    complete_query = f"{prior_summary}\nAdditionally filtering for {summarized_query}"
    if len(resulting_hotels) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_hotels,
            query_summary=f"{complete_query}",
        )

    return SearchResultsOutputModel(
        search_results=resulting_hotels,
        query_summary=f"{complete_query}\nThere are {len(resulting_hotels)} hotels that matched this query!",
    )
