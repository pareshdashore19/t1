from t1.tools.schema.cache import (
    GetCacheInputModel,
    GetCacheOutputModel,
    SaveCacheInputModel,
)
from t1.tools.schema.search_output import SearchResultsOutputModel

cache = {}


def get_results_from_cache(**kwargs: GetCacheInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to get items from the cache

    Examples:
    >>> # Usage Example:
    get_results_from_cache(key=previous_flights)

    >>> # Usage Example:
    get_results_from_cache(key=previous_hotels)

    >>> # Usage Example:
    get_results_from_cache(key=previous_restaurants)

    >>> # Usage Example:
    get_results_from_cache(key=previous_attractions)

    Returns:
        GetCacheOutputModel: Output object which contains the result of the cache query.
    """
    global cache
    input_key = GetCacheInputModel.model_validate(kwargs)
    return cache.get(input_key.key, None)


def save_to_cache(**kwargs: SaveCacheInputModel) -> None:
    """
    Description:
        Use this tool to get items from the cache

    Examples:
    >>> # Usage Example:
    save_to_cache(key="previous_flights", value=previous_flights)

    >>> # Usage Example:
    save_to_cache(key="previous_hotels", value=previous_hotels)

    >>> # Usage Example:
    save_to_cache(key="previous_restaurants", value="previous_restaurants")

    >>> # Usage Example:
    save_to_cache(key="previous_attractions", value="previous_attractions")
    """
    parameters = SaveCacheInputModel.model_validate(kwargs)
    cache[parameters.key] = parameters.value


def reset_cache():
    global cache
    cache = {}


def dump_entire_cache():
    global cache
    return cache


def dump_cache_query():
    global cache
    # Since python 3.7 dict is by default ordereddict
    try:
        return {k: v.query_summary for k, v in cache.items()}
    except Exception as e:
        for k, v in cache.items():
            print(k)
            print(v)
        print("unable to dump data")


def get_cache_for_current_turn():
    global cache
    # Since python 3.7 dict is by default ordereddict
    return {k: v.query_summary for k, v in cache.items()}


def get_cache(arg1):
    return {k: v.query_summary for k, v in arg1.items()}


def retrieve_ground_truth_cache(row):
    global cache
    cache = row["entire_cache_before_current_turn"]

    return cache
