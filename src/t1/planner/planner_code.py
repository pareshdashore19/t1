import ast
import pandas as pd
from google import genai
import json
import logging
import os
import re
from datetime import datetime
import time
from transformers import AutoTokenizer
from typing import Dict, List

from t1.tools.filter_attractions import filter_attractions
from t1.tools.filter_flights import filter_flights
from t1.tools.filter_hotels import filter_hotels
from t1.tools.filter_restaurants import filter_restaurants
from t1.tools.find_nearest import search_nearest
from t1.tools.search_attractions import search_attractions
from t1.tools.search_flights import search_flights
from t1.tools.search_hotels import search_hotels
from t1.tools.search_restaurants import search_restaurants
from t1.tools.find_nearest import search_nearest
from t1.tools.seek_information import seek_information
from t1.tools.adjust_date import adjust_date
from t1.tools.sort_results import sort_results
from t1.tools.cache import get_results_from_cache, save_to_cache
from t1.tools.utils.get_tool_configurations import configure_tools_definitions

from t1.planner.planner_utils import few_shot_examples, few_shot_examples_2

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)


def _configure_domain_tools() -> str:
    """Configure tools ."""

    # Define all available tools
    all_tools = [
        {"tool_name": "search_flights", "tool_func": search_flights},
        {"tool_name": "filter_flights", "tool_func": filter_flights},
        {"tool_name": "search_hotels", "tool_func": search_hotels},
        {"tool_name": "filter_hotels", "tool_func": filter_hotels},
        {"tool_name": "search_restaurants", "tool_func": search_restaurants},
        {"tool_name": "filter_restaurants", "tool_func": filter_restaurants},
        {"tool_name": "find_nearest", "tool_func": search_nearest},
        {"tool_name": "seek_information", "tool_func": seek_information},
        {"tool_name": "adjust_date", "tool_func": adjust_date},
        {"tool_name": "search_attractions", "tool_func": search_attractions},
        {"tool_name": "filter_attractions", "tool_func": filter_attractions},
        {"tool_name": "search_nearest", "tool_func": search_nearest},
        {"tool_name": "sort_results", "tool_func": sort_results},
        {
            "tool_name": "get_results_from_cache",
            "tool_func": get_results_from_cache,
        },
        {"tool_name": "save_to_cache", "tool_func": save_to_cache},
    ]

    print(f"Tools using : {[x['tool_name'] for x in all_tools]}")
    # Get tool configuration
    return configure_tools_definitions(all_tools)


all_tools_config = _configure_domain_tools()


def prompt_reasoning_final(conversation, cache_for_conversation):
    system_prompt = f"""
You are an expert AI travel planner and your responsibility is to generate Python code using APIs or Tools. 
        """

    user_prompt = f"""
Your task is to generate a Python code based on a conversation between the user and the assistant, where the last turn is from the user.
The code typically involves calling one or more tools (functions) to help the user in planning their travel request.
In the Python code, you need to use the following tools:

# TOOL CONFIG
{all_tools_config}

# INSTRUCTIONS
- Track content: Maintain the conversation state across turns and use all known information from earlier in the conversation.
- As soon as the mandatory parameters (non-optional parameters) are all provided (refer to TOOL CONFIG to find mandatory parameters for each tool), generate the appropriate plan using Python code.
- Do NOT modify entity values under any circumstances. Use them exactly as they appear in the conversation while populating attributes in the function during code generation.
    For example, if the city is "new york" (lowercase), do not convert it to "New York" or "NYC".
- Do not fill optional parameters unless they are explicitly provided in the conversation.
- When generating seek_information, only mention mandatory parameters (non-optional parameters) that are missing. Never ask for optional parameters using seek_information. Refer to TOOL CONFIG to figure out what the mandatory parameters (non optional parameters) are and check CONVERSATION to know what parameters have been provided by the user. 
    For example, "seek_information('<explain what mandatory parameters (non-optional parameters) are missing and must be gathered by the assistant>')"
- Only generate the code for the domain which the customer has mentioned in the conversation. For example, if user mentioned only about attractions, don't generate the code with restaurants search. Only if the user mentioned searching for restaurant anywhere in the conversation, then only search for restaurants.
- If a tool result from a previous turn is still valid and relevant, use get_results_from_cache(key="<cache_key>") to retrieve it. Use the cache summary to determine the most appropriate key to select from. If you have many keys in the cache for the same domain. Use the one which would be most relevant.
- If you generate a tool call and its result could be reused later, save it with save_to_cache("<key>",value). Ensure the cache key is unique and avoid naming collision with previously stored cache key name
- If a result has already been stored in the cache for a conversation and no new result needs to be generated, do not regenerate the code. Instead, return the code as "print("No planning needed")"


# OUTPUT FORMAT
- You need to generate the reasoning and the python code. The reasoning should clearly explain the process, steps and the reason behind the python plan that is going to be generated 

The python code should be within the <CODE> </CODE> tags. Note while generating the python code, never have any markdown tags. The code within <CODE> </CODE> tags will be executed, so it should only have executable code.

# EXAMPLES
{few_shot_examples_2}

# CONVERSATION
{conversation}

# CACHE
{cache_for_conversation}

Given the provided conversation and cache summary, generate a Python code for the last user turn.
"""

    messages = system_prompt + "\n" + user_prompt

    return messages


def make_reasoning_prompt(conversation, cache_for_conversation):

    prompt_message = prompt_reasoning_final(conversation, cache_for_conversation)

    return prompt_message


def get_batch_results(prompts):

    CLIENT_RETRIES = 3

    from openai import OpenAI

    model_id = "gpt-5-mini"

    client = OpenAI()
    for attempt in range(CLIENT_RETRIES):
        try:
            response = client.responses.create(
                model=model_id, input=prompts[0], reasoning={"effort": "low"}
            )
            # get the output string
            response = response.output_text
            break
        except Exception as e:
            logging.warning("Error calling OpenAI API:")

    return response
