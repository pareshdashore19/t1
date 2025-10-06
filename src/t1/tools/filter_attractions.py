import os
import re
from datetime import datetime

import pandas as pd

from src.tools.schema.filter_attractions import FilterAttractionsInputModel
from src.tools.schema.search_output import SearchResultsOutputModel


def summarize_query(search_input_filtered):
    result = []
    if "city" in search_input_filtered:
        attraction_city = search_input_filtered["city"]
        if not "state" in search_input_filtered:
            result.append(
                "city: {},".format(
                    attraction_city,
                )
            )
        else:
            attraction_state = search_input_filtered["state"]
            result.append(
                "city: {}, state: {},".format(attraction_city, attraction_state)
            )
    if "state" in search_input_filtered and not "city" in search_input_filtered:
        attraction_state = search_input_filtered["state"]
        result.append("state: {},".format(attraction_state))

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


def filter_attractions(
    **kwargs: FilterAttractionsInputModel,
) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for restaurants based on several criteria such as city, cuisine as well as dietary restrictions.

    Examples:
    >>> # Usage Example:
    filter_attractions(prior_results=attractions_search, type=["Art", "Social"])

    >>> # Usage Example:
    filter_attractions(prior_results=attractions_search, neighborhood=["Venice"],type=["Tourist"])

    >>> # Usage Example:
    filter_attractions(prior_results=attractions_search, attraction_name=["The Exploratorium"])

    >>> # Usage Example:
    filter_attractions(prior_results=attractions_search, type=["Scenery", "Art", "Tourist"])

    >>> # Usage Example:
    filter_attractions(prior_results=attractions_search, type=["Culture", "Historical", "Social"])

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting attractions as well as the summary.
    """
    search_input = FilterAttractionsInputModel.model_validate(kwargs)
    search_input_filtered = {
        k: v for k, v in search_input.dict().items() if v is not None
    }
    all_attractions_df = pd.DataFrame(
        search_input_filtered["prior_results"]["search_results"]
    )
    if len(all_attractions_df) == 0:
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
    mask = pd.Series(True, index=all_attractions_df.index)
    all_attractions_columns = list(all_attractions_df.columns)
    for col, search_query_parameters in search_input_filtered.items():
        if type(search_query_parameters) is list:
            if (
                col == "neighborhood"
                and "neighborhood_attractions" in all_attractions_columns
            ):
                mask &= all_attractions_df["neighborhood_attractions"].isin(
                    search_query_parameters
                )
            else:
                mask &= all_attractions_df[col].isin(search_query_parameters)

        elif type(search_query_parameters) is str:
            mask &= all_attractions_df[col] == search_query_parameters
    resulting_attractions = (all_attractions_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)
    prior_summary = search_input_filtered["prior_results"]["query_summary"]
    prior_summary = re.sub(
        r"There are.*?that matched this query!\.?$", "", prior_summary.strip()
    )
    complete_query = f"{prior_summary}\nAdditionally filtering for {summarized_query}"

    if len(resulting_attractions) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_attractions,
            query_summary=f"{complete_query}",
        )

    return SearchResultsOutputModel(
        search_results=resulting_attractions,
        query_summary=f"{complete_query}\nThere are {len(resulting_attractions)} attractions that match this query!",
    )
