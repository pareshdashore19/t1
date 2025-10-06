import pandas as pd
from adjust_date import adjust_date
from cache import get_results_from_cache, save_to_cache
from filter_attractions import filter_attractions
from filter_flights import filter_flights
from filter_hotels import filter_hotels
from filter_restaurants import filter_restaurants
from find_nearest import search_nearest
from search_attractions import search_attractions
from search_flights import search_flights
from search_hotels import search_hotels
from search_restaurants import search_restaurants
from seek_information import seek_information
from sort_results import sort_results

from utils.get_tool_configurations import configure_tools_definitions

tools = [
    {"tool_name": "search_flights", "tool_func": search_flights},
    {"tool_name": "filter_flights", "tool_func": filter_flights},
    {"tool_name": "search_hotels", "tool_func": search_hotels},
    {"tool_name": "filter_hotels", "tool_func": filter_hotels},
    {"tool_name": "search_restaurants", "tool_func": search_restaurants},
    {"tool_name": "filter_restaurants", "tool_func": filter_restaurants},
    {"tool_name": "search_attractions", "tool_func": search_attractions},
    {"tool_name": "filter_attractions", "tool_func": filter_attractions},
    {"tool_name": "sort_results", "tool_func": sort_results},
    {"tool_name": "save_to_cache", "tool_func": save_to_cache},
    {"tool_name": "get_results_from_cache", "tool_func": get_results_from_cache},
    {"tool_name": "search_nearest", "tool_func": search_nearest},
    {"tool_name": "adjust_date", "tool_func": adjust_date},
    {"tool_name": "seek_information", "tool_func": seek_information},
]

departure_flights = search_flights(
    start_airport_city="Greensboro",
    end_airport_city="Pittsburgh",
    departure_date=["May 11, 2025"],
)
return_flights = search_flights(
    start_airport_city="Pittsburgh",
    end_airport_city="Greensboro",
    departure_date=["May 24, 2025"],
)
filtered_departure_flights = filter_flights(
    prior_results=departure_flights, airline=["AB", "AC"]
)
save_to_cache(key="departure_flights", value=departure_flights)
save_to_cache(key="return_flights", value=return_flights)

departure_flights = get_results_from_cache(key="departure_flights")
return_flights = get_results_from_cache(key="return_flights")
filtered_departure_flights = filter_flights(
    prior_results=departure_flights, flight_class=["first"]
)
filtered_return_flights = filter_flights(
    prior_results=return_flights, flight_class=["first"]
)
save_to_cache(key="filtered_departure_flights", value=filtered_departure_flights)
save_to_cache(key="filtered_return_flights", value=filtered_return_flights)

hotels = search_hotels(
    city="Pittsburgh",
    checkin_date=["May 20, 2025"],
    checkout_date=["May 29, 2025"],
    stars=[3, 3],
    neighborhood=["Downtown Pittsburgh"],
)

filtered_hotels = filter_hotels(prior_results=hotels, gym_present=True)
restaurants = search_restaurants(city="Pittsburgh", cuisine=["Indian", "Indonesian"])
filtered_restaurants = filter_restaurants(
    prior_results=restaurants, has_tomato_allergy_options=True
)
attractions = search_attractions(city="Pittsburgh")
save_to_cache(key="hotels", value=hotels)
print("hotels")
print(departure_flights.query_summary)
print(hotels.query_summary)
print(filtered_departure_flights.query_summary)
print(filtered_hotels.query_summary)
print(restaurants.query_summary)
print(filtered_restaurants.query_summary)
print(attractions.query_summary)

nearest_hotels_attraction = search_nearest(
    attractions=attractions, hotels=filtered_hotels, groupBy="hotel"
)
print(nearest_hotels_attraction.query_summary)

nearest_hotels_restaurant = search_nearest(
    restaurants=restaurants, hotels=filtered_hotels, groupBy="restaurant"
)
print(nearest_hotels_attraction.query_summary)
print("Nearest hotels")
print(nearest_hotels_restaurant.query_summary)
print(nearest_hotels_restaurant.search_results)

"""
result = configure_tools_definitions(tools)
print(result)

initial_search = search_flights(
    start_airport_code="EYW",
    end_airport_city="Fayetteville",
    arrival_time=["08:00", "12:00"],
    departure_date=["2025-08-03", "2025-08-04"],
    airline=["AF", "AC"],
)
# print("Key west")
# print(initial_search.query_summary)
save_to_cache(key="flights", value=initial_search)
cache_flights = get_results_from_cache(key="flights")
# Get summary
for key in cache_flights.search_results[0]:
    if not "Unnamed" in key:
        print(key)
# Gets you summary
# print(cache_flights.query_summary)

test_search = search_flights(
    start_airport_city="Phoenix",
    end_airport_city="Houston",
    departure_date=["2025-03-01", "2025-03-02", "2025-03-03", "2025-03-04"],
    airline=["AE"],
    num_layovers=[2],
    layover_1_city=["Chicago"],
    layover_2_city=["Detroit", "Dallas"],
)


filtered_flights = filter_flights(
    prior_results=cache_flights,
    flight_class=["first", "business"],
    arrival_time=["00:00", "18:45"],
    num_layovers=[0],
    duration_minutes=300,
    budget=1025,
)
sorted_filtered_flights = sort_results(
    results=cache_flights, column="departure_time", ascending=True
)
# print(sorted_filtered_flights)
hotel_search = search_hotels(
    city="Boston",
    checkin_date=["2025-05-01"],
    checkout_date=["2025-05-04"],
    stars=[3, 4],
)

print("hotels")
# print(hotel_search)

# print(hotel_search.query_summary)
filtered_hotel_search = filter_hotels(
    prior_results=hotel_search,
    smoking_allowed=False,
    breakfast_included=True,
    has_skiing_lodging=False,
    rating=[4, 5],
    neighborhood=["Staten Island"],
)
filtered_hotel_search = filter_hotels(
    prior_results=hotel_search,
    smoking_allowed=False,
    breakfast_included=True,
    is_pet_friendly=True,
    budget=350,
)
# print(filtered_hotel_search.query_summary)

restaurant_search = search_restaurants(city="Boston", has_halal_options=True)
# print(restaurant_search.query_summary)
filtered_restaurant_search = filter_restaurants(
    prior_results=restaurant_search, budget=700
)
# print(filtered_restaurant_search.query_summary)

attractions_search = search_attractions(state="MA")
# print(attractions_search.query_summary)

hotels = search_hotels(
    city="Boston", checkin_date=["August 1, 2025"], checkout_date=["August 7, 2025"]
)

nearest_restaurants = search_nearest(
    restaurants=filtered_restaurant_search,
    hotels=hotels,
    groupBy="restaurant",
)

sorted_restaurants = sort_results(
    results=nearest_restaurants, column="rating_restaurants", ascending=True
)
print("sorted results are")
# print(sorted_restaurants)

departure_flights = get_results_from_cache(key="departure_flights")
print("departure_flights")
print(departure_flights)
filtered_departure_flights = filter_flights(
    prior_results=departure_flights, flight_class=["business"]
)
save_to_cache(key="filtered_departure_flights", value=filtered_flights)
return_flights = get_results_from_cache(key="return_flights")
filtered_return_flights = filter_flights(
    prior_results=return_flights, flight_class=["business"]
)
save_to_cache(key="filtered_return_flights", value=filtered_return_flights)

nearest_restaurants = filter_restaurants(
    prior_results=nearest_restaurants, neighborhood=["Fenway-Kenmore"]
)
sorted_results = sort_results(
    results=nearest_restaurants, column="price_per_person", ascending=False
)
# print(sorted_results)

attractions = search_attractions(
    city="Detroit", attraction_name=["Mission Inn Hotel & Spa"], type=["Touristy"]
)
print(attractions)

restaurants = search_restaurants(city="Columbus", cuisine=["Lithuanian"])
save_to_cache(key="restaurants", value=restaurants)
print("here are german restaurants")
print(restaurants)

restaurants = get_results_from_cache(key="restaurants")
filtered_restaurants = filter_restaurants(prior_results=restaurants, cuisine=["German"])
save_to_cache(key="filtered_restaurants", value=filtered_restaurants)

restaurants = get_results_from_cache(key="filtered_restaurants")
filtered_restaurants1 = filter_restaurants(prior_results=restaurants, rating=[3.5, 5])
save_to_cache(key="filtered_restaurants1", value=filtered_restaurants1)

departure_flights = search_flights(
    start_airport_city="Reno",
    end_airport_city="Jacksonville",
    departure_date=["May 9, 2025"],
    arrival_time=["12:00 AM", "10:16 PM"],
)

return_flights = search_flights(
    start_airport_city="San Francisco",
    end_airport_city="Reno",
    departure_date=["May 31, 2025"],
)

departure_flights = search_flights(
    start_airport_city="Reno",
    end_airport_city="Fort Wayne",
    departure_date=["May 18, 2025"],
)
return_flights = search_flights(
    start_airport_city="Fort Wayne",
    end_airport_city="Reno",
    departure_date=["May 31, 2025"],
)
save_to_cache(key="departure_flights", value=departure_flights)
save_to_cache(key="return_flights", value=return_flights)

departure_flights = get_results_from_cache(key="departure_flights")
return_flights = get_results_from_cache(key="return_flights")
filtered_departure_flights = filter_flights(
    prior_results=departure_flights, flight_class=["first"]
)
filtered_return_flights = filter_flights(
    prior_results=return_flights, flight_class=["first"]
)
save_to_cache(key="filtered_departure_flights", value=filtered_departure_flights)
save_to_cache(key="filtered_return_flights", value=filtered_return_flights)
"""
"""
attractions_search = search_attractions(state="MA")
print(attractions_search.query_summary)

filter_attractions_search = filter_attractions(
    prior_results=attractions_search, type=["Sports", "Culture"]
)
print(filter_attractions_search.query_summary)

save_to_cache(key="initial_attractions", value=attractions_search)

save_to_cache(key="filter_attractions", value=filter_attractions_search)
res = get_results_from_cache(key="initial_attractions")
# print(res)
print("--" * 100)
second = get_results_from_cache(key="filter_attractions")

nearest_hotels = search_nearest(
    hotels=filtered_hotel_search, attractions=attractions_search, sortBy="hotel_name"
)
print(nearest_hotels.query_summary)
print("nearest hotels")

nearest_restaurants = search_nearest(
    restaurants=filtered_restaurant_search,
    attractions=attractions_search,
    sortBy="restaurant_name",
)
# print(nearest_hotels)
print("-" * 50)
print(nearest_restaurants.query_summary)

addition_filtered_restaurants = filter_restaurants(
    prior_results=nearest_restaurants, has_gluten_free_options=True
)
print(len(addition_filtered_restaurants.search_results))

sorted_results = sort_results(
    results=nearest_restaurants, column="price_per_person", ascending=False
)
# print(sorted_results)

current_date = "April 10, 2025"
new_date = adjust_date(date=current_date, delta_days=-16)
print(new_date)

print(adjust_date(date="Mar 1, 2024", delta_days=2))

print(adjust_date(date="2025-04-17", delta_days=2))
"""
