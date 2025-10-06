import os

import pandas as pd

from src.tools.schema.find_nearest import FindNearestInputModel
from src.tools.schema.search_output import SearchResultsOutputModel

HOTEL_ATTRACTIONS = os.getenv("HOTEL_ATTRACTIONS")
HOTEL_RESTAURANTS = os.getenv("HOTEL_RESTAURANTS")
RESTAURANT_ATTRACTIONS = os.getenv("RESTAURANT_ATTRACTIONS")
hotel_attractions_df = pd.read_csv(HOTEL_ATTRACTIONS)
hotel_restaurants_df = pd.read_csv(HOTEL_RESTAURANTS)
restaurant_attractions_df = pd.read_csv(RESTAURANT_ATTRACTIONS)


def run_query(
    merged_df, results_dict, first_category, second_category, groupBy, summary
):
    groupBy = "{}_name".format(groupBy)
    first_df = pd.DataFrame(results_dict[first_category]["search_results"])
    second_df = pd.DataFrame(results_dict[second_category]["search_results"])
    current_query_summary = "{}. Moreover, {}".format(
        results_dict[first_category]["query_summary"],
        results_dict[second_category]["query_summary"],
    )
    if not first_df.empty and not second_df.empty:
        merged_filtered_df = merged_df[
            merged_df["{}_name".format(first_category[:-1])].isin(
                first_df["{}_name".format(first_category[:-1])]
            )
            & merged_df["{}_name".format(second_category[:-1])].isin(
                second_df["{}_name".format(second_category[:-1])]
            )
        ]
    elif not first_df.empty:
        merged_filtered_df = merged_df[
            merged_df["{}_name".format(first_category[:-1])].isin(
                first_df["{}_name".format(first_category[:-1])]
            )
        ]
    elif not second_df.empty:
        merged_filtered_df = merged_df[
            merged_df["{}_name".format(second_category[:-1])].isin(
                second_df["{}_name".format(second_category[:-1])]
            )
        ]
    else:
        return SearchResultsOutputModel(search_results=[], query_summary=summary)

    sorted_matches = merged_filtered_df.sort_values(
        [groupBy, "distance_miles"]
    ).reset_index(drop=True)
    return SearchResultsOutputModel(
        search_results=sorted_matches.to_dict(orient="records"), query_summary=summary
    )


def search_nearest(
    **kwargs: FindNearestInputModel,
) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to find the nearest attractions, hotels or restaurants.

    Examples:
    >>> # Usage Example:
    search_nearest(hotels=searched_hotels, attractions=searched_attractions, groupBy="hotel")

    >>> # Usage Example:
    search_nearest(hotels=searched_hotels, attractions=searched_attractions, groupBy="attraction")

    >>> # Usage Example:
    search_nearest(restaurants=searched_restaurants, attractions=searched_attraction,groupBy="attraction")

    >>> # Usage Example:
    search_nearest(restaurants=searched_restaurants, attractions=searched_attraction,groupBy="restaurant")

    >>> # Usage Example:
    search_nearest(hotels=searched_hotels, restaurants=searched_restaurants, groupBy="restaurant")

    >>> # Usage Example:
    search_nearest(hotels=searched_hotels, restaurants=searched_restaurants, groupBy="hotel")

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting attractions as well as the summary.
    """
    results = FindNearestInputModel.model_validate(kwargs)
    results_dict = {
        field: value
        for field, value in results.model_dump().items()
        if value is not None
    }
    groupBy = results_dict["groupBy"].value
    if "hotels" in results_dict and "attractions" in results_dict:
        hotels_summary = results_dict["hotels"]["query_summary"]
        attractions_summary = results_dict["attractions"]["query_summary"]

        if groupBy == "hotel":
            query_summary = f"Hotels near attractions with the following criteria:\n{hotels_summary}\n{attractions_summary}"

        if groupBy == "attraction":
            query_summary = f"Attractions near hotels with the following criteria:\n{attractions_summary}\n{hotels_summary}"

        return run_query(
            hotel_attractions_df,
            results_dict,
            "hotels",
            "attractions",
            groupBy,
            query_summary,
        )

    if "hotels" in results_dict and "restaurants" in results_dict:

        hotels_summary = results_dict["hotels"]["query_summary"]
        restaurants_summary = results_dict["restaurants"]["query_summary"]

        if groupBy == "hotel":
            query_summary = f"Hotels near restaurants with the following criteria:\n{hotels_summary}\n{restaurants_summary}"

        if groupBy == "restaurant":
            query_summary = f"Restaurants near hotels with the following criteria:\n{restaurants_summary}\n{hotels_summary}"
        return run_query(
            hotel_restaurants_df,
            results_dict,
            "hotels",
            "restaurants",
            groupBy,
            query_summary,
        )
    if "attractions" in results_dict and "restaurants" in results_dict:

        attractions_summary = results_dict["attractions"]["query_summary"]
        restaurants_summary = results_dict["restaurants"]["query_summary"]

        if groupBy == "attractions":
            query_summary = f"Attractions near restaurants with the following criteria:\n{attractions_summary}\n{restaurants_summary}"

        if groupBy == "restaurant":
            query_summary = f"Restaurants near attractions with the following criteria:\n{restaurants_summary}\n{attractions_summary}"
        return run_query(
            restaurant_attractions_df,
            results_dict,
            "attractions",
            "restaurants",
            groupBy,
            query_summary,
        )
