import os
from datetime import datetime

import pandas as pd

from src.tools.schema.search_attractions import SearchAttractionsInputModel
from src.tools.schema.search_output import SearchResultsOutputModel

all_attractions_df = pd.read_csv(os.getenv("ALL_ATTRACTIONS"))


def summarize_query(search_input_filtered):
    result = []
    if "city" in search_input_filtered:
        attraction_city = search_input_filtered["city"]
        if not "state" in search_input_filtered:
            result.append(
                "Attraction search results in {}.".format(
                    attraction_city,
                )
            )
        else:
            attraction_state = search_input_filtered["state"]
            result.append(
                "Attraction search results in {}, {}.".format(
                    attraction_city, attraction_state
                )
            )
    if "state" in search_input_filtered and not "city" in search_input_filtered:
        attraction_state = search_input_filtered["state"]
        result.append("Attraction search results in {}.".format(attraction_state))

    if "neighborhood" in search_input_filtered:
        result.append(
            "neighborhood(s): [{}],".format(
                ", ".join(search_input_filtered["neighborhood"])
            )
        )

    if "type" in search_input_filtered:
        result.append(
            "attraction type(s): [{}],".format(", ".join(search_input_filtered["type"]))
        )

    if "attraction_name" in search_input_filtered:
        result.append(
            "attraction name(s): [{}],".format(
                ", ".join(search_input_filtered["attraction_name"])
            )
        )

    final_result = " ".join(result)
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."

    return final_result


def search_attractions(
    **kwargs: SearchAttractionsInputModel,
) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for restaurants based on several criteria such as city, cuisine as well as dietary restrictions.

    Examples:
    >>> # Usage Example:
    search_attractions(city="Dallas", type=["Art", "Social"])

    >>> # Usage Example:
    search_attractions(city="Los Angeles", neighborhood=["Venice"],type=["Tourist"])

    >>> # Usage Example:
    search_attractions(city="San Francisco", attraction_name=["The Exploratorium"])

    >>> # Usage Example:
    search_attractions(city="Boston", type=["Scenery", "Art", "Tourist"])

    >>> # Usage Example:
    search_attractions(city="Phoenix", type=["Culture", "Historical", "Social"])

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting attractions as well as the summary.
    """
    search_input = SearchAttractionsInputModel.model_validate(kwargs)
    search_input_filtered = {
        k: v for k, v in search_input.dict().items() if v is not None
    }
    mask = pd.Series(True, index=all_attractions_df.index)
    for col, search_query_parameters in search_input_filtered.items():
        if type(search_query_parameters) is list:
            mask &= all_attractions_df[col].isin(search_query_parameters)

        elif type(search_query_parameters) is str:
            mask &= all_attractions_df[col] == search_query_parameters
    resulting_attractions = (all_attractions_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)
    if len(resulting_attractions) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_attractions,
            query_summary=f"{summarized_query}",
        )

    return SearchResultsOutputModel(
        search_results=resulting_attractions,
        query_summary=f"{summarized_query}\nThere are {len(resulting_attractions)} attractions that matched this query!",
    )
