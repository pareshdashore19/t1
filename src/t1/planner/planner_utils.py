few_shot_examples = """
# EXAMPLE 1

## CONVERSATION:
[{"assistant" : "assistant: Hi! What's your travel plan?"},
{"user": "I'm traveling with 6 people to Boston and we need a hotel."}]

## CACHE SUMMARY:
{}

## OUTPUT:

<REASONING>
We don't have any cache saved. As per the tool definition of search_hotel, I need to know the city and dates to call the tool. I just have the city which is a mandatory parameter. Number of people is an optional parameter so I cannot call the search_hotel tool given the information provided. Also there is no cache present with hotels that I could use.
</REASONING>

<CODE>
seek_information("We need to ask for the check-in and check-out dates")
</CODE>

# EXAMPLE 2

## CONVERSATION:
[{"assistant" : "assistant: Hi! What's your travel plan?"},
{"user": "traveling with 3 people to NYC. Help me find a hotel"},
{"assistant": "How many rooms do you need?"},
{"user": "We need 3 rooms."},
{"assistant": "Okay, got it! What's your check-in and check-out date?"},
{"user": "We're checking in on June 2, 2023 and checking out on June 4, 2023."},
{"assistant": "Are you looking for any specific amenities in the hotel?"},
{"user": "Yes, we need a hotel with wifi and a gym."}]

## CACHE SUMMARY:
{"hotels" : "some hotel summary that suggests that we already have saved results of hotel search to NYC for 3 people and 3 rooms for checkin on June 2, 2023 and checking out on June 4, 2023. Also while storing cache I need to make sure that the key name is unique and is not present in the cache currently.}

## OUTPUT:

<REASONING>
I already have a cache and the key "hotels" could be used as it is already has results for the hotel search for NYC for 3 people, 3 rooms with checkin and checkout dates. I will use these results and then filter the results with wifi and gym. I will not search for hotel in cache.
</REASONING>

<CODE>
"hotels = get_results_from_cache(key="hotels")
filtered_hotels = filter_hotels(prior_results=hotels, free_wifi_included=True, gym_present=True)
save_to_cache(key="filtered_hotels", value=filtered_hotels)"
</CODE>


# EXAMPLE 3

## CONVERSATION:
[{"assistant" : "assistant: Hi! What's your travel plan?"},
{"user": "I need a hotel from May 12, 2025 to May 14, 2025 in Dallas"}]

## CACHE SUMMARY:
{}

## OUTPUT:

<REASONING>
I have all mandatory parameters for search_hotels. I can call the tool
</REASONING>

<CODE>
hotels = search_hotels(city="Dallas", checkin_date=["May 12, 2025"], checkout_date=["May 14, 2025"])
save_to_cache(key="hotels", value=hotels)
</CODE>

# EXAMPLE 4

## CONVERSATION:
[{"assistant": "Welcome to our travel assistant. How can I help you today?"},
{"user": "I'm planning a trip to New York and I'd like to book a economy flight from Delhi."},
{"assistant": "That sounds like a great trip. What are your travel dates?"},
{"user": "I'm looking to fly from May 10, 2025 to May 19, 2025. Also looking for  2 star hotel"}]

## CACHE SUMMARY:
{}

## OUTPUT:

<REASONING>
There is no flight cache present. I have all mandatory parameters for search_flights. User has also provided the flight_class parameter. I can call the tool, search_flights and generate a code to find departure and return flight. I also have all the mandatory parameters to call tool, search_hotels along with optional parameter star. 
</REASONING>

<CODE>
flights = search_flights(start_airport_city="Delhi", end_airport_city="New York", departure_date=["May 10, 2025"],flight_class=["economy"])
save_to_cache(key="flights", value=flights)
return_flights = search_flights(start_airport_city="New York", end_airport_city="Delhi", departure_date=["May 19, 2025"],flight_class=["economy"])
save_to_cache(key="return_flights", value=return_flights)
hotels = search_hotels(city="New York", checkin_date=["May 10, 2025"], checkout_date=["May 19, 2025"], stars=[2, 2])
save_to_cache(key="hotels", value=hotels)
</CODE>

# EXAMPLE 5

## CONVERSATION:
[{"assistant": "Welcome to our travel assistant. How can I help you today?"},
{"user": "I'm planning a trip to New Delhi and I'd like to book a economy flight from Mumbai. Also book hotel for me. I will depart on November 15, 2025"}]

## CACHE SUMMARY:
{}

## OUTPUT:

<REASONING>
There is no flight cache or hotel cache present. I have all mandatory parameters for search_flights, but I don't have mandatory parameters i.e checkout_date for search_flights. I will call search_flight and seek_information to request checkout_date.
</REASONING>

<CODE>
flights = search_flights(start_airport_city="Mumbai", end_airport_city="New Delhi", departure_date=["November 15, 2025"])
save_to_cache(key="flights", value=flights)
seek_information("We need to ask for the check-out dates for the hotel.")
</CODE>

# EXAMPLE 6

## CONVERSATION:
[{"user": "I'm planning a business trip from Dallas to Austin and I need a flight and a hotel with a gym."},
{"assistant": "What are your travel dates?"},
{"user": "I'm traveling on August 5, 2028 and returning on August 15, 2028"},
{"assistant": "What's your preferred airline?"},
{"user": "I prefer Tomato Airline."},
{"assistant": "Great! And for hotels, what's your preferred neighborhood in Austin?"},
{"user": "North Austin would be ideal."},
{"assistant: What kind of restaurant are you looking for?"},
{"user: Something with Chinese and a 2 rating or higher with access to the hotel."}
]

## CACHE SUMMARY:
{"flight_1": "Results of the flight from Dallas to Austin. It has 5 results",
"flight_2": "Results of the flight from Austin to Dallas. It has 30 results",
"hotels" : "Result of hotel for Austin. It has 33 results"
"filtered_flights1":"Result of flights from Dallas to Austin with Tomato Airline. It has 1 results,
"filtered_flights1":"Result of flights from Austin to Dallas with Tomato Airline. It has 2 results,
"filtered_hotels": "Results of hotel in Austin in the North Austin neighborhood}

## OUTPUT:

<REASONING>
We have many keys stored in the cache but we don't have any cache for the restaurants that could be used. I do have 2 cache fo hotels. The most relevant cache and the updated one is filtered_hotels. It is also something I will use as it already has hotels filtered with North Austin neighborhood as there is no point in doing a search again. User wants restaurant near the hotel. We have all the mandatory parameters for search_restaurants. I can use it and then find the restaurants. Since the max rating can be 5, I would use the rating as [2,5]. I could use the cache filtered hotels and then use search_nearest function to find a restaurant near the hotel. Since I am going to find restaurant near the hotel, the groupby would contain restaurant. Also while storing cache I need to make sure that the key names are unique and is not present in the cache currently.
</REASONING>

<CODE>
restaurants = search_restaurants(city="Austin", cuisine=["Chinese"], rating=[2, 5])
save_to_cache(key="restaurants", value=restaurants)
hotels = get_results_from_cache(key="filtered_hotels")
nearest_restaurants = search_nearest(hotels=hotels, restaurants=restaurants, groupBy="restaurant")
save_to_cache(key="nearest_restaurants", value=nearest_restaurants)
</CODE>

# EXAMPLE 7

## CONVERSATION:
[{"assistant": "How can I help you",
{"user": "I want to fly to Chicago from Philadelphia on "April 13, 2025"},
{"assistant": "Any preferred class?"},
{"user":"no, but I prefer aisle seat"}}]

## CACHE SUMMARY:
{"flight": "summary of flights from chicago to Philadelphia on "April 13, 2025."}

## OUTPUT:

<REASONING>
We already have stored in cache previously flight results.  We can't filter the results because filter_flights doesn't allow to filter flights on seat type. We don't need to get it from cache as it would not used . Saving same results again to cache is not useful. I can generate- "print("No planning needed")"
</REASONING>

<CODE>
print("No planning needed")
</CODE>

# EXAMPLE 8

## CONVERSATION:
[{"assistant": " Welcome to our travel assistant. How can I help you today?}, {'user': " I'm planning a trip to New York and I'd like to book a economy flight from Boston."}, {'assistant': ' That sounds like a great trip. What are your travel dates?'}, {'user': " I'm looking to depart on May 17, 2025 and return on May 19, 2025."}, {'assistant': ' Okay, got it. And how many travelers are there?'}, {'user': ' There are 1 of us.'}]

## CACHE SUMMARY:
{"departure_flights": 'Flight search results from Boston to New York, departing on date(s) May 17, 2025. in economy "return_flights": 'Flight search results from Boston to New York, departing on May 19, 2025, flight classes is economy'}

## OUTPUT:

<REASONING>
We already have stored in cache previously flight results.  We can't filter the results for number of passenger as the filter_flights doesn't take such parameter as input. No additional planning is needed and I would not get anything from cache.)"
</REASONING>

<CODE>
print("No planning needed")
</CODE>

# EXAMPLE 9

## CONVERSATION:
[{"assistant": " Hi, I'm here to help. What's your travel plan?"}, {"user": " I'm planning a family reunion in San Francisco and need flights from Philadelphia for 3 people."}, {"assistant": "What are your travel dates?"}, {"user": " We're looking to depart on May 12, 2025 and return on May 15, 2025."}, {"assistant": "And what class of service are you interested in?"}, {"user": "We'd like business class."}, {"assistant": "Alright, and for accommodations, what kind of hotel are you looking for?"}, {'user': "A 4 star hotel with a kids club, pool, and wifi."}]

## CACHE SUMMARY:
{"flights": "Flight search results from Philadelphia to San Francisco, departing on May 12, 2025", "return_flights": "Flight search results from San Francisco to Philadelphia, departing on date(s) May 15, 2025]", "filtered_flights": "Flight search results from Philadelphia to San Francisco, departing on date(s) May 12, 2025and filtered on business class', "filtered_return_flights": "Flight search results from San Francisco to Philadelphia, departing on date(s) May 15, 2025 filtered on business class"}

## OUTPUT:

<REASONING>
We have cache for flight for flights which can't be used. We can search fo hotels as we have all the mandatory parameters. We will take num_people as 3 because 3 people are flying so it means 3 people will be staying.  Also while storing cache I need to make sure that the key name is unique and is not present in the cache currently.
</REASONING>

<CODE>
hotels = search_hotels(city="San Francisco", checkin_date=["May 12, 2025"], checkout_date=["May 15, 2025"], num_people=3, stars=[4, 5], has_kids_club=True, pool_present=True, free_wifi_included=True)
save_to_cache(key="hotels", value=hotels)
</CODE>

# EXAMPLE 10

## CONVERSATION:
[{"assistant": "Welcome, how can I help with your travel plans?"}, {"user': "I'm planning a solo trip to Anchorage and need a flight from Philadelphia."}, {"assistant": "What are your travel dates for this trip?'}, {"user": "I'm looking to depart on May 11, 2025 and return on May 25, 2025."}, {"assistant": "And what class of service are you interested in?"}, {"user": "I prefer business class."}, {"assistant": "Alright, and for accommodations, what type of hotel are you looking for?"}, {"user": "A 2 star hotel with a gym and wifi. And I'm interested in Culinary attractions."}]

# EXAMPLE 11

## CONVERSATION:
[{'assistant': ' Hi there! What can I help you with?'}, {'user': " I'm planning a family vacation to Tucson and I need a flight from Cleveland with a kid-friendly airline."}, {'assistant': ' What dates are you thinking of traveling?'}, {'user': 'depart May 8, 2026 to May 19, 2026.'}]

## CACHE SUMMARY:
{}

## OUTPUT:

<REASONING>
We have all the mandatory parameter to call search flight which is checkin and checkout date. We don't have any parameter to take kid-friendly airline into account for the search_hotel. So I will just ignore it.   
</REASONING>

<CODE>
flights = search_flights(start_airport_city="Cleveland", end_airport_city="Tucson", departure_date=["May 8, 2026"], arrival_date=["May 19, 2026"])
save_to_cache(key="flights", value=flights)
return_flights = search_flights(start_airport_city="Tucson", end_airport_city="Cleveland", departure_date=["May 19, 2026"])
save_to_cache(key="return_flights", value=return_flights)
</CODE>

# EXAMPLE 12

## CONVERSATION
[{"assistant":  "Hello, how can I assist you with your travel needs?"}, {"user": "I'm looking for a flight to Stockton from Orlando for 4 people."}, {'assistant': "What's your preferred departure date?"}, {"user": "We're looking to depart as soon as possible, around May 16, 2025 and coming back on May 22, 2025."}, {"assistant": "Okay, and what's your budget for the flight?"}, {"user": "We're aiming to spend around 875."}, {"assistant": "Got it. Now, for hotels, what area in Stockton are you interested in?"}, {"user": "We'd like to stay in Downtown Stockton with access to Art attractions."}, {"assistant": "And what amenities are you looking for in the hotel?"}, {"user": "Wifi, a gym, and a rooftop bar would be great. Also, we're interested in visiting Bob Hope Theatre."}]

## CACHE SUMMARY:
{"departure_flights": "Flight search results from Orlando to Stockton, departing on date(s) May 16, 2025.", "return_flights": "Flight search results from Orlando to Stockton, departing on date(s) May 22, 2025", "filtered_departure_flights": 'Flight search results from Orlando to Stockton, departing on date(s) May 16, 2025.Additionally filtering for budget: $875", "filtered_return_flights": "Flight search results from Orlando to Stockton, departing on date(s) May 22, 2025.\nAdditionally filtering for budget: $875", "hotels": "Hotel search results in Stockton from check-in date(s) May 16, 2025 to check-out date(s) May 22, 2025., neighborhood(s): Downtown Stockton.\nThere are 24 hotel(s) that matched this query!", "attractions": "Attraction search results in Stockton. attraction type(s) Art.\nThere are 2 attractions that matched this query!", "nearest_hotels": "Hotels near attractions with the following criteria:\nHotel search results in Stockton from check-in date(s) May 16, 2025 to check-out date(s) May 22, 2025. neighborhood(s): [Downtown Stockton].\nThere are 24 hotel(s) that matched this query!\nAttraction search results in Stockton. attraction type(s): Art.\nThere are 2 attractions that matched this query!'}

## OUTPUT:

<REASONING>
 The most recent cache, nearest_hotels should be used as user wants to stay in neighborhood Downtown Stockton. I should filter the result with wifi, gym and rooftop bar. I should also get attraction from cache with the key "attractions". User has not stated if he want to stay close to Bob Hope Theatre, so i should just find this attraction. Also while storing cache I need to make sure that the key name is unique and is not present in the cache currently.
</REASONING>

<CODE>
hotels = get_results_from_cache(key="nearest_hotels")
filtered_hotels = filter_hotels(prior_results=hotels, free_wifi_included=True, gym_present=True, has_rooftop_bar=True)
save_to_cache(key="filtered_hotels", value=filtered_hotels)
attractions = get_results_from_cache(key="attractions")
attractions = search_attractions(city="Stockton", attraction_name=["Bob Hope Theatre"])
save_to_cache(key="attractions", value=attractions)
</CODE>

# EXAMPLE 13

## CONVERSATION:
{"assistant": "Hi, what brings you here today?"}, {"user": "I'm planning a business meeting in Miami and need a hotel with meeting rooms."}, {"assistant": "What are your travel dates?"}, {"user": "Check-in is September 10, 2025 and check-out is September 21, 2025."}, {"assistant": "How many rooms do you need for your team and what's your budget per night?"}, {"user": "3 rooms and around 1025."}, {"assistant": "I see. Are you looking for any specific amenities for your meeting?'}, {'user': ' Yes, meeting rooms and wifi are must-haves."}]

## CACHE SUMMARY:
{'hotels': 'Hotel search results in Miami from check-in date(s) September 10, 2025 to check-out date(s) September 21, 2025. There are 75 hotel(s) that matched this query!", "filtered_hotels": "Hotel search results in Miami from check-in date(s) September 10, 2025 to check-out date(s) September 21, 2025\n\nAdditionally filtering for Number of room(s): 3, budget: $1025.\nThere are 58 hotels that matched this query!'}

## OUTPUT:

<REASONING>
I have 2 cache stored for the hotel. The most updated cache is filtered_hotels will be used, since it is filtered with 2 rooms and the budget already. There is no point of doing a hotel search again. We can filter the results of the filtered_hotels cache with wifi and meeting rooms. Also I update the cache, I will use a unique key name that is not present in cache summary.
</REASONING>

<CODE>
hotels = get_results_from_cache(key="filtered_hotels")
filtered_hotels_2= filter_hotels(prior_results=hotels, has_meeting_rooms=True, free_wifi_included=True)
save_to_cache(key="filtered_hotels_2", value=filtered_hotels_2)

"""


conversation = """
[{'assistant': ' Hello, what brings you here today?'}, {'user': " I'm looking for a hotel in Agra for my anniversary, can you help me?"}, {'assistant': ' Congratulations on your anniversary! What are your check-in and check-out dates?'}, {'user': " We're planning to check-in on May 7, 2025 and check-out on May 16, 2025. Also need to check Taj Mahal"}]
"""

cache_for_conversation = """{}"""

few_shot_examples_2 = """
# EXAMPLE 1

## CONVERSATION:
[{"assistant" : "assistant: Hi! What's your travel plan?"},
{"user": "I'm traveling with 6 people to Boston and we need a hotel."}]

## CACHE SUMMARY:
{}

## OUTPUT:

<CODE>
seek_information("We need to ask for the check-in and check-out dates")
</CODE>

# EXAMPLE 2

## CONVERSATION:
[{"assistant" : "assistant: Hi! What's your travel plan?"},
{"user": "traveling with 3 people to NYC. Help me find a hotel"},
{"assistant": "How many rooms do you need?"},
{"user": "We need 3 rooms."},
{"assistant": "Okay, got it! What's your check-in and check-out date?"},
{"user": "We're checking in on June 2, 2023 and checking out on June 4, 2023."},
{"assistant": "Are you looking for any specific amenities in the hotel?"},
{"user": "Yes, we need a hotel with wifi and a gym."}]

## CACHE SUMMARY:
{"hotels" : "some hotel summary that suggests that we already have saved results of hotel search to NYC for 3 people and 3 rooms for checkin on June 2, 2023 and checking out on June 4, 2023. Also while storing cache I need to make sure that the key name is unique and is not present in the cache currently.}

## OUTPUT:

<CODE>
"hotels = get_results_from_cache(key="hotels")
filtered_hotels = filter_hotels(prior_results=hotels, free_wifi_included=True, gym_present=True)
save_to_cache(key="filtered_hotels", value=filtered_hotels)"
</CODE>


# EXAMPLE 3

## CONVERSATION:
[{"assistant" : "assistant: Hi! What's your travel plan?"},
{"user": "I need a hotel from May 12, 2025 to May 14, 2025 in Dallas"}]

## CACHE SUMMARY:
{}

## OUTPUT:

<CODE>
hotels = search_hotels(city="Dallas", checkin_date=["May 12, 2025"], checkout_date=["May 14, 2025"])
save_to_cache(key="hotels", value=hotels)
</CODE>

# EXAMPLE 4

## CONVERSATION:
[{"assistant": "Welcome to our travel assistant. How can I help you today?"},
{"user": "I'm planning a trip to New York and I'd like to book a economy flight from Delhi."},
{"assistant": "That sounds like a great trip. What are your travel dates?"},
{"user": "I'm looking to fly from May 10, 2025 to May 19, 2025. Also looking for  2 star hotel"}]

## CACHE SUMMARY:
{}

## OUTPUT:

<CODE>
flights = search_flights(start_airport_city="Delhi", end_airport_city="New York", departure_date=["May 10, 2025"],flight_class=["economy"])
save_to_cache(key="flights", value=flights)
return_flights = search_flights(start_airport_city="New York", end_airport_city="Delhi", departure_date=["May 19, 2025"],flight_class=["economy"])
save_to_cache(key="return_flights", value=return_flights)
hotels = search_hotels(city="New York", checkin_date=["May 10, 2025"], checkout_date=["May 19, 2025"], stars=[2, 2])
save_to_cache(key="hotels", value=hotels)
</CODE>

# EXAMPLE 5

## CONVERSATION:
[{"assistant": "Welcome to our travel assistant. How can I help you today?"},
{"user": "I'm planning a trip to New Delhi and I'd like to book a economy flight from Mumbai. Also book hotel for me. I will depart on November 15, 2025"}]

## CACHE SUMMARY:
{}

## OUTPUT:

<CODE>
flights = search_flights(start_airport_city="Mumbai", end_airport_city="New Delhi", departure_date=["November 15, 2025"])
save_to_cache(key="flights", value=flights)
seek_information("We need to ask for the check-out dates for the hotel.")
</CODE>

# EXAMPLE 6

## CONVERSATION:
[{"user": "I'm planning a business trip from Dallas to Austin and I need a flight and a hotel with a gym."},
{"assistant": "What are your travel dates?"},
{"user": "I'm traveling on August 5, 2028 and returning on August 15, 2028"},
{"assistant": "What's your preferred airline?"},
{"user": "I prefer Tomato Airline."},
{"assistant": "Great! And for hotels, what's your preferred neighborhood in Austin?"},
{"user": "North Austin would be ideal."},
{"assistant: What kind of restaurant are you looking for?"},
{"user: Something with Chinese and a 2 rating or higher with access to the hotel."}
]

## CACHE SUMMARY:
{"flight_1": "Results of the flight from Dallas to Austin. It has 5 results",
"flight_2": "Results of the flight from Austin to Dallas. It has 30 results",
"hotels" : "Result of hotel for Austin. It has 33 results"
"filtered_flights1":"Result of flights from Dallas to Austin with Tomato Airline. It has 1 results,
"filtered_flights1":"Result of flights from Austin to Dallas with Tomato Airline. It has 2 results,
"filtered_hotels": "Results of hotel in Austin in the North Austin neighborhood}

## OUTPUT:

<CODE>
restaurants = search_restaurants(city="Austin", cuisine=["Chinese"], rating=[2, 5])
save_to_cache(key="restaurants", value=restaurants)
hotels = get_results_from_cache(key="filtered_hotels")
nearest_restaurants = search_nearest(hotels=hotels, restaurants=restaurants, groupBy="restaurant")
save_to_cache(key="nearest_restaurants", value=nearest_restaurants)
</CODE>

# EXAMPLE 7

## CONVERSATION:
[{"assistant": "How can I help you",
{"user": "I want to fly to Chicago from Philadelphia on "April 13, 2025"},
{"assistant": "Any preferred class?"},
{"user":"no, but I prefer aisle seat"}}]

## CACHE SUMMARY:
{"flight": "summary of flights from chicago to Philadelphia on "April 13, 2025."}

## OUTPUT:

<CODE>
print("No planning needed")
</CODE>

# EXAMPLE 8

## CONVERSATION:
[{"assistant": " Welcome to our travel assistant. How can I help you today?}, {'user': " I'm planning a trip to New York and I'd like to book a economy flight from Boston."}, {'assistant': ' That sounds like a great trip. What are your travel dates?'}, {'user': " I'm looking to depart on May 17, 2025 and return on May 19, 2025."}, {'assistant': ' Okay, got it. And how many travelers are there?'}, {'user': ' There are 1 of us.'}]

## CACHE SUMMARY:
{"departure_flights": 'Flight search results from Boston to New York, departing on date(s) May 17, 2025. in economy "return_flights": 'Flight search results from Boston to New York, departing on May 19, 2025, flight classes is economy'}

## OUTPUT:

<CODE>
print("No planning needed")
</CODE>

# EXAMPLE 9

## CONVERSATION:
[{"assistant": " Hi, I'm here to help. What's your travel plan?"}, {"user": " I'm planning a family reunion in San Francisco and need flights from Philadelphia for 3 people."}, {"assistant": "What are your travel dates?"}, {"user": " We're looking to depart on May 12, 2025 and return on May 15, 2025."}, {"assistant": "And what class of service are you interested in?"}, {"user": "We'd like business class."}, {"assistant": "Alright, and for accommodations, what kind of hotel are you looking for?"}, {'user': "A 4 star hotel with a kids club, pool, and wifi."}]

## CACHE SUMMARY:
{"flights": "Flight search results from Philadelphia to San Francisco, departing on May 12, 2025", "return_flights": "Flight search results from San Francisco to Philadelphia, departing on date(s) May 15, 2025]", "filtered_flights": "Flight search results from Philadelphia to San Francisco, departing on date(s) May 12, 2025and filtered on business class', "filtered_return_flights": "Flight search results from San Francisco to Philadelphia, departing on date(s) May 15, 2025 filtered on business class"}

## OUTPUT:

<CODE>
hotels = search_hotels(city="San Francisco", checkin_date=["May 12, 2025"], checkout_date=["May 15, 2025"], num_people=3, stars=[4, 5], has_kids_club=True, pool_present=True, free_wifi_included=True)
save_to_cache(key="hotels", value=hotels)
</CODE>

# EXAMPLE 10

## CONVERSATION:
[{"assistant": "Welcome, how can I help with your travel plans?"}, {"user': "I'm planning a solo trip to Anchorage and need a flight from Philadelphia."}, {"assistant": "What are your travel dates for this trip?'}, {"user": "I'm looking to depart on May 11, 2025 and return on May 25, 2025."}, {"assistant": "And what class of service are you interested in?"}, {"user": "I prefer business class."}, {"assistant": "Alright, and for accommodations, what type of hotel are you looking for?"}, {"user": "A 2 star hotel with a gym and wifi. And I'm interested in Culinary attractions."}]

# EXAMPLE 11

## CONVERSATION:
[{'assistant': ' Hi there! What can I help you with?'}, {'user': " I'm planning a family vacation to Tucson and I need a flight from Cleveland with a kid-friendly airline."}, {'assistant': ' What dates are you thinking of traveling?'}, {'user': 'depart May 8, 2026 to May 19, 2026.'}]

## CACHE SUMMARY:
{}

## OUTPUT:

<CODE>
flights = search_flights(start_airport_city="Cleveland", end_airport_city="Tucson", departure_date=["May 8, 2026"], arrival_date=["May 19, 2026"])
save_to_cache(key="flights", value=flights)
return_flights = search_flights(start_airport_city="Tucson", end_airport_city="Cleveland", departure_date=["May 19, 2026"])
save_to_cache(key="return_flights", value=return_flights)
</CODE>

# EXAMPLE 12

## CONVERSATION
[{"assistant":  "Hello, how can I assist you with your travel needs?"}, {"user": "I'm looking for a flight to Stockton from Orlando for 4 people."}, {'assistant': "What's your preferred departure date?"}, {"user": "We're looking to depart as soon as possible, around May 16, 2025 and coming back on May 22, 2025."}, {"assistant": "Okay, and what's your budget for the flight?"}, {"user": "We're aiming to spend around 875."}, {"assistant": "Got it. Now, for hotels, what area in Stockton are you interested in?"}, {"user": "We'd like to stay in Downtown Stockton with access to Art attractions."}, {"assistant": "And what amenities are you looking for in the hotel?"}, {"user": "Wifi, a gym, and a rooftop bar would be great. Also, we're interested in visiting Bob Hope Theatre."}]

## CACHE SUMMARY:
{"departure_flights": "Flight search results from Orlando to Stockton, departing on date(s) May 16, 2025.", "return_flights": "Flight search results from Orlando to Stockton, departing on date(s) May 22, 2025", "filtered_departure_flights": 'Flight search results from Orlando to Stockton, departing on date(s) May 16, 2025.Additionally filtering for budget: $875", "filtered_return_flights": "Flight search results from Orlando to Stockton, departing on date(s) May 22, 2025.\nAdditionally filtering for budget: $875", "hotels": "Hotel search results in Stockton from check-in date(s) May 16, 2025 to check-out date(s) May 22, 2025., neighborhood(s): Downtown Stockton.\nThere are 24 hotel(s) that matched this query!", "attractions": "Attraction search results in Stockton. attraction type(s) Art.\nThere are 2 attractions that matched this query!", "nearest_hotels": "Hotels near attractions with the following criteria:\nHotel search results in Stockton from check-in date(s) May 16, 2025 to check-out date(s) May 22, 2025. neighborhood(s): [Downtown Stockton].\nThere are 24 hotel(s) that matched this query!\nAttraction search results in Stockton. attraction type(s): Art.\nThere are 2 attractions that matched this query!'}

## OUTPUT:

<CODE>
hotels = get_results_from_cache(key="nearest_hotels")
filtered_hotels = filter_hotels(prior_results=hotels, free_wifi_included=True, gym_present=True, has_rooftop_bar=True)
save_to_cache(key="filtered_hotels", value=filtered_hotels)
attractions = get_results_from_cache(key="attractions")
attractions = search_attractions(city="Stockton", attraction_name=["Bob Hope Theatre"])
save_to_cache(key="attractions", value=attractions)
</CODE>

# EXAMPLE 13

## CONVERSATION:
{"assistant": "Hi, what brings you here today?"}, {"user": "I'm planning a business meeting in Miami and need a hotel with meeting rooms."}, {"assistant": "What are your travel dates?"}, {"user": "Check-in is September 10, 2025 and check-out is September 21, 2025."}, {"assistant": "How many rooms do you need for your team and what's your budget per night?"}, {"user": "3 rooms and around 1025."}, {"assistant": "I see. Are you looking for any specific amenities for your meeting?'}, {'user': ' Yes, meeting rooms and wifi are must-haves."}]

## CACHE SUMMARY:
{'hotels': 'Hotel search results in Miami from check-in date(s) September 10, 2025 to check-out date(s) September 21, 2025. There are 75 hotel(s) that matched this query!", "filtered_hotels": "Hotel search results in Miami from check-in date(s) September 10, 2025 to check-out date(s) September 21, 2025\n\nAdditionally filtering for Number of room(s): 3, budget: $1025.\nThere are 58 hotels that matched this query!'}

## OUTPUT:

<CODE>
hotels = get_results_from_cache(key="filtered_hotels")
filtered_hotels_2= filter_hotels(prior_results=hotels, has_meeting_rooms=True, free_wifi_included=True)
save_to_cache(key="filtered_hotels_2", value=filtered_hotels_2)
</CODE>

"""
