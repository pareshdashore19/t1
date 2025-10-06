import os
import re
from datetime import datetime

import pandas as pd

from data.ontology.restaurant import DIETARY_OPTIONS
from src.tools.schema.filter_restaurants import FilterRestaurantsInputModel
from src.tools.schema.search_output import SearchResultsOutputModel

all_restaurants_df = pd.read_csv(os.getenv("ALL_RESTAURANTS"))


def summarize_query(search_input_filtered):
    result = []
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


def filter_restaurants(
    **kwargs: FilterRestaurantsInputModel,
) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for restaurants based on several criteria such as city, cuisine as well as dietary restrictions.

    Examples:

    >>> # Usage Example:
    filter_restaurants(cuisine=["Indian", "Chinese"])

    >>> # Usage Example:
    filter_restaurants(cuisine=["Indian", "Mexican"], has_tomato_allergy_options=True, has_shell_fish_allergy_options=True)

    >>> # Usage Example:
    filter_restaurants(budget=350, rating=[4,5])

    >>> # Usage Example:
    filter_restaurants(rating=[2,4], has_nut_allergy_options=True, has_tomato_allergy_options=True, has_nightshade_allergy_options=True)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting restaurants as well as the summary.
    """
    search_input = FilterRestaurantsInputModel.model_validate(kwargs)
    search_input_filtered = {
        k: v for k, v in search_input.dict().items() if v is not None
    }
    all_restaurants_df = pd.DataFrame(
        search_input_filtered["prior_results"]["search_results"]
    )
    if len(all_restaurants_df) == 0:
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
    mask = pd.Series(True, index=all_restaurants_df.index)
    all_restaurant_columns = list(all_restaurants_df.columns)
    for col, search_query_parameters in search_input_filtered.items():
        if type(search_query_parameters) is list:
            if col == "rating":
                if "rating_restaurants" in all_restaurant_columns:
                    mask &= (
                        all_restaurants_df["rating_restaurants"]
                        >= search_query_parameters[0]
                    ) & (
                        all_restaurants_df["rating_restaurants"]
                        <= search_query_parameters[1]
                    )
                else:
                    mask &= (all_restaurants_df[col] >= search_query_parameters[0]) & (
                        all_restaurants_df[col] <= search_query_parameters[1]
                    )
            elif (
                col == "neighborhood"
                and "neighborhood_restaurants" in all_restaurant_columns
            ):
                mask &= all_restaurants_df["neighborhood_restaurants"].isin(
                    search_query_parameters
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
    prior_summary = search_input_filtered["prior_results"]["query_summary"]
    prior_summary = re.sub(
        r"There are.*?that matched this query!\.?$", "", prior_summary.strip()
    )
    complete_query = f"{prior_summary}\nAdditionally filtering for {summarized_query}"

    if len(resulting_restaurants) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_restaurants,
            query_summary=f"{complete_query}",
        )

    return SearchResultsOutputModel(
        search_results=resulting_restaurants,
        query_summary=f"{complete_query}\nThere are {len(resulting_restaurants)} restaurants that matched this query!",
    )
