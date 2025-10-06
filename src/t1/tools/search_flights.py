import os
from datetime import datetime

import pandas as pd

from src.tools.schema.search_flights import SearchFlightsInputModel
from src.tools.schema.search_output import SearchResultsOutputModel

all_flights_df = pd.read_csv(os.getenv("ALL_FLIGHTS"))
all_flights_df["departure_time"] = pd.to_datetime(
    all_flights_df["departure_time"], format="%H:%M:%S"
).dt.time
all_flights_df["arrival_time"] = pd.to_datetime(
    all_flights_df["arrival_time"], format="%H:%M:%S"
).dt.time


def summarize_query(search_input_filtered):
    result = []
    if "start_airport_code" in search_input_filtered:
        start_airport_city = search_input_filtered["start_airport_code"]
    if "start_airport" in search_input_filtered:
        start_airport_city = search_input_filtered["start_airport"]
    if "start_airport_city" in search_input_filtered:
        start_airport_city = search_input_filtered["start_airport_city"]

    if "end_airport_code" in search_input_filtered:
        end_airport_city = search_input_filtered["end_airport_code"]
    if "end_airport" in search_input_filtered:
        end_airport_city = search_input_filtered["end_airport"]
    if "end_airport_city" in search_input_filtered:
        end_airport_city = search_input_filtered["end_airport_city"]
    departure_date = ", ".join(search_input_filtered["departure_date"])
    result.append(
        "Flight search results from {} to {}, departing on date(s) [{}].".format(
            start_airport_city,
            end_airport_city,
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


def search_flights(**kwargs: SearchFlightsInputModel) -> SearchResultsOutputModel:
    """
    Description:
        Use this tool to search for flights based on several criteria such as preference of flight class, airlines, number of layovers, layover cities, departure time, arrival time, price of flight ticket, etc. Note - One of start_airport_city, start_airport or airport_code MUST be provided.

    Examples:
    >>> # Usage Example:
    search_flights(start_airport_city="Key West",end_airport_city="Fayetteville",departure_date=["2025-08-03", "2025-08-04"])

    >>> # Usage Example:
    search_flights(start_airport_city="Los Angeles",end_airport_city="Seattle",departure_date=["2025-09-01"],airline=["AB", "AA"])

    >>> # Usage Example:
    search_flights(start_airport_city="San Francisco",end_airport_city="Boston",arrival_date=["2026-01-02"],arrival_time=["08:00:00", "12:00:00"],departure_date=["2026-01-01", "2026-01-02"],airline=["AA", "AB", "AC", "AD"])

    >>> # Usage Example:
    search_flights(start_airport_city="Phoenix",end_airport_city="Memphis",arrival_time=["00:00:00", "14:00:00"],departure_date=["2025-10-01", "2025-10-02", "2025-10-03"],airline=["AE"], num_layovers=[1], layover_1_city=["Chicago"])

    >>> # Usage Example:
    search_flights(start_airport_city="Boston",end_airport_city="Houston",departure_date=["2025-03-01", "2025-03-02", "2025-03-03", "2025-03-04"],airline=["AE"], num_layovers=[2], layover_1_city=["Chicago"], layover_2_city=["Detroit", "Dallas"])

    Returns:
        SearchResultsOutputModel: Output object which contains the resulting flights as well as the summary.
    """
    search_input = SearchFlightsInputModel.model_validate(kwargs)
    search_input_filtered = {
        k: v for k, v in search_input.dict().items() if v is not None
    }
    mask = pd.Series(True, index=all_flights_df.index)
    for col, search_query_parameters in search_input_filtered.items():
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

    if len(resulting_flights) == 0:
        return SearchResultsOutputModel(
            search_results=resulting_flights,
            query_summary=f"{summarized_query}",
        )
    result = SearchResultsOutputModel(
        search_results=resulting_flights,
        query_summary=f"{summarized_query}\nThere are {len(resulting_flights)} flight(s) that matched this query!",
    )
    return result
