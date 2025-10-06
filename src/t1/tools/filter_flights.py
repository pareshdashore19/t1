import re
from datetime import datetime

import pandas as pd

from t1.tools.schema.filter_flights import FilterFlightsInputModel
from t1.tools.schema.search_output import SearchResultsOutputModel


def summarize_query(search_input_filtered):
    result = []
    start_airport_city = ""
    if (
        "start_airport_code" in search_input_filtered
        or "start_airport" in search_input_filtered
        or "start_airport_city" in search_input_filtered
    ):
        if "start_airport_code" in search_input_filtered:
            start_airport_city = search_input_filtered["start_airport_code"]
        if "start_airport" in search_input_filtered:
            start_airport_city = search_input_filtered["start_airport"]
        if "start_airport_city" in search_input_filtered:
            start_airport_city = search_input_filtered["start_airport_city"]
    if len(start_airport_city) > 0:
        result.append("departure from: {},".format(start_airport_city))

    end_airport_city = ""
    if "end_airport_code" in search_input_filtered:
        end_airport_city = search_input_filtered["end_airport_code"]
    if "end_airport" in search_input_filtered:
        end_airport_city = search_input_filtered["end_airport"]
    if "end_airport_city" in search_input_filtered:
        end_airport_city = search_input_filtered["end_airport_city"]
    if len(end_airport_city) > 0:
        result.append("arrives at {},".format(end_airport_city))

    if "departure_date" in search_input_filtered:
        departure_date = ", ".join(search_input_filtered["departure_date"])
        result.append(
            "departing on date(s): [{}],".format(
                departure_date,
            )
        )
    if "departure_time" in search_input_filtered:
        departure_time = ", ".join(search_input_filtered["departure_time"])
        result.append("departure time range: [{}],".format(departure_time))

    if "arrival_date" in search_input_filtered:
        arrival_date = ", ".join(search_input_filtered["arrival_date"])
        result.append("arriving on date(s): [{}],".format(arrival_date))

    if "arrival_time" in search_input_filtered:
        arrival_time = ", ".join(search_input_filtered["arrival_time"])
        result.append("arrival time range: [{}],".format(arrival_time))

    if "duration_minutes" in search_input_filtered:
        duration = search_input_filtered["duration_minutes"]
        result.append("max flight duration: {} minutes,".format(duration))

    if "airline" in search_input_filtered:
        airline = ", ".join(search_input_filtered["airline"])
        result.append("airline(s): [{}],".format(airline))

    if "flight_class" in search_input_filtered:
        flight_class = ", ".join(search_input_filtered["flight_class"])
        result.append("flight classes: [{}],".format(flight_class))

    if "flight_id" in search_input_filtered:
        flight_id = ", ".join(search_input_filtered["flight_id"])
        result.append("flight ID(s): [{}],".format(flight_id))

    if "budget" in search_input_filtered:
        result.append("budget: ${},".format(search_input_filtered["budget"]))

    if "num_layovers" in search_input_filtered:
        result.append(
            "max number of layover(s): {},".format(
                max(search_input_filtered["num_layovers"])
            )
        )
        if "layover_1_city" in search_input_filtered:
            result.append(
                "first layover cities: {},".format(
                    ", ".join(search_input_filtered["layover_1_city"])
                )
            )
            if "layover_2_city" in search_input_filtered:
                result.append(
                    "second layover cities: {},".format(
                        ", ".join(search_input_filtered["layover_2_city"])
                    )
                )
        if 1 in search_input_filtered["num_layovers"]:
            if "layover_1_duration_minutes" in search_input_filtered:
                layover_1_duration_minutes = search_input_filtered[
                    "layover_1_duration_minutes"
                ]
                result.append(
                    "max layover 1 duration: {} minutes,".format(
                        layover_1_duration_minutes
                    )
                )
        if 2 in search_input_filtered["num_layovers"]:
            if "layover_2_duration_minutes" in search_input_filtered:
                layover_2_duration_minutes = search_input_filtered[
                    "layover_2_duration_minutes"
                ]
                result.append(
                    "max layover 2 duration: {} minutes,".format(
                        layover_2_duration_minutes
                    )
                )

    final_result = " ".join(result)
    if final_result.endswith(","):
        final_result = final_result[:-1] + "."

    return final_result


def filter_flights(**kwargs: FilterFlightsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to filter out flights based on several criteria such as preference of flight class, airlines, number of layovers, layover cities, departure time, arrival time, price of flight ticket, etc.

    Examples:
    >>> # Usage Example:
    filter_flights(prior_results=search_results,airline=["AB", "AC"])

    >>> # Usage Example:
    filter_flights(prior_results=search_results, arrival_date=["2026-01-02"],arrival_time=["08:00:00", "12:00:00"],departure_date=["2026-01-01", "2026-01-02"],airline=["AA", "AB", "AC", "AD"], duration_minutes=240)

    >>> # Usage Example:
    filter_flights(prior_results=search_results,arrival_time=["00:00:00", "14:00:00"],departure_date=["2025-10-01", "2025-10-02", "2025-10-03"],airline=["AE"], num_layovers=[1], layover_1_city=["Chicago"])

    >>> # Usage Example:
    filter_flights(prior_results=search_results,start_airport_city="Phoenix",end_airport_city="Houston",departure_date=["2025-03-01", "2025-03-02", "2025-03-03", "2025-03-04"],airline=["AE"], num_layovers=[2], layover_1_city=["Chicago"], layover_2_city=["Detroit", "Dallas"])

    >>> # Usage Example:
    filter_flights(prior_results=search_results, budget=750, flight_class=["Economy", "Business"])

    Returns:
       SearchResultsOutputModel: Output object which contains the resulting flights as well as the summary of the query.
    """
    search_input = FilterFlightsInputModel.model_validate(kwargs)
    search_input_filtered = {
        k: v for k, v in search_input.dict().items() if v is not None
    }
    all_flights_df = pd.DataFrame(
        search_input_filtered["prior_results"]["search_results"]
    )
    if len(all_flights_df) == 0:
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
    mask = pd.Series(True, index=all_flights_df.index)
    for col, search_query_parameters in search_input_filtered.items():
        if col == "prior_results":
            continue
        if isinstance(search_query_parameters, list):
            if col == "flight_class":
                flight_class_mask = pd.Series(False, index=all_flights_df.index)
                for parameter in search_query_parameters:
                    flight_class_mask |= (
                        all_flights_df[f"{parameter}_class_option_present"] == True
                    )
                mask &= flight_class_mask
            elif col == "departure_time" or col == "arrival_time":
                time_objects = [
                    datetime.strptime(t, "%H:%M:%S").time()
                    for t in search_query_parameters
                ]
                flight_time_mask = all_flights_df[col].apply(
                    lambda t: time_objects[0] <= t <= time_objects[1]
                )
                mask &= flight_time_mask
            else:
                mask &= all_flights_df[col].isin(search_query_parameters)

        elif isinstance(search_query_parameters, int):
            if col == "budget":
                if not "flight_class" in search_input_filtered:
                    mask &= (
                        (
                            all_flights_df["economy_class_price"]
                            <= search_query_parameters
                        )
                        | (
                            all_flights_df["business_class_price"]
                            <= search_query_parameters
                        )
                        | (
                            all_flights_df["first_class_price"]
                            <= search_query_parameters
                        )
                    )
                else:
                    flight_classes = search_input_filtered["flight_class"]
                    flight_price_mask = pd.Series(False, index=all_flights_df.index)
                    for each_class in flight_classes:
                        flight_price_mask |= (
                            all_flights_df[f"{each_class}_class_price"]
                            <= search_query_parameters
                        )
                    mask &= flight_price_mask
            elif col == "duration_minutes":
                mask &= all_flights_df[col] <= search_query_parameters
            elif (
                col == "layover_1_duration_minutes"
                or col == "layover_2_duration_minutes"
            ):
                layover_duration_mask = all_flights_df[col] <= search_query_parameters
                mask &= layover_duration_mask
        elif isinstance(search_query_parameters, str):
            mask &= all_flights_df[col] == search_query_parameters
    resulting_flights = (all_flights_df[mask]).to_dict(orient="records")
    summarized_query = summarize_query(search_input_filtered)
    prior_summary = search_input_filtered["prior_results"]["query_summary"]

    prior_summary = re.sub(
        r"There are.*?that matched this query!\.?$", "", prior_summary.strip()
    )
    complete_query = f"{prior_summary}\nAdditionally filtering for {summarized_query}"

    if len(resulting_flights) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_flights,
            query_summary=f"{complete_query}",
        )
    result = SearchResultsOutputModel(
        search_results=resulting_flights,
        query_summary=f"{complete_query}\nThere are {len(resulting_flights)} flight(s) that matched this query!",
    )
    return result
