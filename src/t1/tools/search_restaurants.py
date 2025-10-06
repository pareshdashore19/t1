import os
from datetime import datetime

import pandas as pd

from data.ontology.restaurant import DIETARY_OPTIONS
from t1.tools.schema.search_output import SearchResultsOutputModel
from t1.tools.schema.search_restaurants import SearchRestaurantsInputModel

all_restaurants_df = pd.read_csv(os.getenv("ALL_RESTAURANTS"))


def summarize_query(search_input_filtered):
    result = []
    restaurant_city = search_input_filtered["city"]
    result.append(
        "Restaurant search results in {}.".format(
            restaurant_city,
        )
    )
    if "neighborhood" in search_input_filtered:
        result.append(
            "neighborhood(s): [{}],".format(
                ", ".join(search_input_filtered["neighborhood"])
            )
        )

    if "cuisine" in search_input_filtered:
        result.append(
            "cuisine(s): [{}],".format(", ".join(search_input_filtered["cuisine"]))
        )

    if "rating" in search_input_filtered:
        res = [str(s) for s in search_input_filtered["rating"]]
        result.append("rating range: [{}],".format(", ".join(res)))

    if "restaurant_name" in search_input_filtered:
        result.append(
            "restaurant name(s): [{}],".format(
                ", ".join(search_input_filtered["restaurant_name"])
            )
        )

    if "budget" in search_input_filtered:
        result.append("budget: ${},".format(search_input_filtered["budget"]))

    dietary_list = [i for i in DIETARY_OPTIONS]
    for dietary_option in dietary_list:
        if dietary_option in search_input_filtered:
            if search_input_filtered[dietary_option]:
                result.append(dietary_option + ",")

    final_result = " ".join(result)
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."

    return final_result


def search_restaurants(
    **kwargs: SearchRestaurantsInputModel,
) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for restaurants based on several criteria such as city, cuisine as well as dietary restrictions.

    Examples:
    >>> # Usage Example:
    search_restaurants(city="Dallas", has_vegetarian_options=True)

    >>> # Usage Example:
    search_restaurants(city="Los Angeles",cuisine=["Indian", "Chinese"])

    >>> # Usage Example:
    search_restaurants(city="San Francisco", cuisine=["Thai"], budget=300, rating=[3,5])

    >>> # Usage Example:
    search_restaurants(city="Boston",cuisine=["Mexican", "Ethiopian"], budget=40, has_vegan_options=True, has_dairy_allergy_options=True)

    >>> # Usage Example:
    search_restaurants(city="Phoenix",budget=1000, has_gluten_free_options=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting hotels as well as the summary.
    """
    search_input = SearchRestaurantsInputModel.model_validate(kwargs)
    search_input_filtered = {
        k: v for k, v in search_input.dict().items() if v is not None
    }
    mask = pd.Series(True, index=all_restaurants_df.index)
    for col, search_query_parameters in search_input_filtered.items():
        if type(search_query_parameters) is list:
            if col == "rating":
                mask &= (all_restaurants_df[col] >= search_query_parameters[0]) & (
                    all_restaurants_df[col] <= search_query_parameters[1]
                )
            else:
                mask &= all_restaurants_df[col].isin(search_query_parameters)

        elif type(search_query_parameters) is int:
            if col == "budget":
                mask &= (
                    all_restaurants_df["price_per_person"] <= search_query_parameters
                )

        elif (
            type(search_query_parameters) is str
            or type(search_query_parameters) is bool
        ):
            mask &= all_restaurants_df[col] == search_query_parameters
    resulting_restaurants = (all_restaurants_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)

    if len(resulting_restaurants) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_restaurants,
            query_summary=f"{summarized_query}",
        )

    return SearchResultsOutputModel(
        search_results=resulting_restaurants,
        query_summary=f"{summarized_query}\nThere are {len(resulting_restaurants)} restaurants that matched this query!",
    )
