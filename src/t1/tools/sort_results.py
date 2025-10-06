import re

import pandas as pd

from t1.tools.schema.search_output import SearchResultsOutputModel
from t1.tools.schema.sort_results import SortResultsInputModel


def sort_results(
    **kwargs: SortResultsInputModel,
) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to sort results based on the domain.
        Sortable columns for flights: "economy_class_price", "business_class_price", "first_class_price", "num_layovers", "layover_1_duration_minutes", "layover_2_duration_minutes", "departure_date", "arrival_date", "departure_time", "arrival_time", "duration_minutes"
        Sortable columns for hotels: "price_per_night", "rating_hotels", "stars", "max_occupancy", "num_rooms_available", "start_date_available", "end_date_available"
        Sortable columns for restaurants: "price_per_person", "rating_restaurants"


    Examples:
    >>> # Usage Example:
    sort_results(results=searched_hotels, column="price_per_night", ascending=True)

    >>> # Usage Example:
    sort_results(results=searched_restaurants, column="price_per_person", ascending=False)

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting attractions as well as the summary.
    """
    input_data = SortResultsInputModel.model_validate(kwargs)
    results = input_data.results.search_results
    prior_summary = input_data.results.query_summary
    column = input_data.column
    ascending = input_data.ascending

    pattern = r"(There are.*?that matched this query!\.?)$"
    if ascending:
        new_text = f"\nResults sorted by {column} in ascending order.\n"
        complete_query = re.sub(pattern, new_text + r"\1", prior_summary)
    else:
        new_text = f"\nResults sorted by {column} in descending order.\n"
        complete_query = re.sub(pattern, new_text + r" \1", prior_summary)

    if len(results) == 0:
        return SearchResultsOutputModel(
            search_results=[], query_summary=f"{complete_query}"
        )
    results_df = pd.DataFrame(results)
    if (column == "rating_restaurants" or column == "rating_hotels") and (
        not column in list(results_df.columns)
    ):
        column = "rating"

    sorted_results_df = results_df.sort_values(by=column, ascending=ascending)
    return SearchResultsOutputModel(
        search_results=sorted_results_df.to_dict(orient="records"),
        query_summary=f"{complete_query}",
    )
