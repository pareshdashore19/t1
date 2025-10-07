import ast
import pandas as pd
from google import genai
import json
import logging
import os
import re
from datetime import datetime
import time
# from eiffel import EiffelClient
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

from t1.planner.planner_utils import (
    few_shot_examples,few_shot_examples_2
)

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
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

all_tools_config=_configure_domain_tools()
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
    
        # messages = [
        #     {"role": "system", "content": system_prompt},
        #     {"role": "user", "content": user_prompt},
        # ]
        messages= system_prompt+"\n"+user_prompt
    
        
        return messages

class PlanLLMGenerator:
    def __init__(self, tokeniser_path: str):

        # Configure tools based on domain
        self.tool_config = self._configure_domain_tools()

        # Set up LLM client
        self.gen_args = {
            "max_tokens": 7000,
            "top_k": 10,
            "temperature": 0.1,
            "random_seed": 64,
        }
        self.client = EiffelClient(url="tool-driven-s1-1k-32k-inference-service.llm-pretraining.svc.cluster.local:9000",generation_args=self.gen_args)
        self.tokenizer = AutoTokenizer.from_pretrained(tokeniser_path)

    def _extract_domain_from_path(self) -> str:
        """Extract domain from the template path."""
        # Use the first template path to determine domain
        filename = os.path.basename(self.template_json_paths[0])
        # Extract the domain(s) from template file name
        match = re.search(r"(.+)_template", filename.split("_raw_")[0])
        if match:
            return match.group(1)
        return "unknown"

    def _configure_domain_tools(self) -> str:
        """Configure tools ."""

        # Define all available tools
        all_tools = [
            {"tool_name": "search_flights", "tool_func": search_flights},
            {"tool_name": "filter_flights", "tool_func": filter_flights},
            {"tool_name": "search_hotels", "tool_func": search_hotels},
            {"tool_name": "filter_hotels", "tool_func": filter_hotels},
            {"tool_name": "search_restaurants", "tool_func": search_restaurants},
            {"tool_name": "filter_restaurants", "tool_func": filter_restaurants},
            {"tool_name": "search_nearest", "tool_func": search_nearest},
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

    def generate_plan(self, conversation, cache_for_conversation) -> Dict:
        """Generate plans for each turn in the template using LLM."""

        system_prompt = f"""
You are an expert AI travel planner and your responsibility is to generate Python code using APIs or Tools. 
"""

        user_prompt = f"""
Your task is to generate a Python code based on a conversation between the user and the assistant, where the last turn is from the user.
The code typically involves calling one or more tools (functions) to help the user in planning their travel request.
In the Python code, you need to use the following tools:

# TOOL CONFIG
{self.tool_config}

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

The reasoning should be within the <REASONING> </REASONING> tags and the python code should be within the <CODE> </CODE> tags. Note while generating the python code, never have any markdown tags.

# EXAMPLES
{few_shot_examples}

# CONVERSATION
{conversation}

# CACHE
{cache_for_conversation}

Given the provided conversation and cache summary, generate a Python code for the last user turn.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )
        print(f"Total token count: {len(self.tokenizer.encode(inputs))}")

        response_text = self.client.infer(inputs)
        """
        import requests

        url = "http://localhost:8000/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "text": inputs,
            "sampling_params": {
                "max_new_tokens": 1024,
                "top_k": 10,
                "temperature": 0.1,
            },
        }
        response = requests.post(url, headers=headers, json=data)
        response_text = response.json()["text"]
        """

        return response_text
    
    def generate_plan_zero_shot(self, conversation, cache_for_conversation):
        """Generate plans for each turn in the template using LLM."""
        user_prompt = f"""
You are an expert AI travel planner and your responsibility is to generate Python code using APIs or Tools. 
Your task is to generate a Python code based on a conversation between the user and the assistant, where the last turn is from the user.
The code typically involves calling one or more tools (functions) to help the user in planning their travel request.
In the Python code, you need to use the following tools:

# TOOL CONFIG
{self.tool_config}

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
- You need to generate only the python code. The python code should be within the <CODE> </CODE> tags. Note while generating the python code, never have any markdown tags.

# EXAMPLES
{few_shot_examples_2}

# CONVERSATION
{conversation}

# CACHE
{cache_for_conversation}

Given the provided conversation and cache summary, generate a Python code for the last user turn.
"""
        # messages = [
        #     {"role": "user", "content": user_prompt},
        # ]

        # inputs = self.tokenizer.apply_chat_template(
        #     messages, add_generation_prompt=True, tokenize=False
        # )
    
        print(f"Total token count: {len(self.tokenizer.encode(user_prompt))}")
        response_text = self.client.infer(user_prompt)
        return response_text


    def prompt_reasoning(self, conversation, cache_for_conversation):
        system_prompt = f"""
You are an expert AI travel planner and your responsibility is to generate Python code using APIs or Tools. 
        """
    
        user_prompt = f"""
Your task is to generate a Python code based on a conversation between the user and the assistant, where the last turn is from the user.
The code typically involves calling one or more tools (functions) to help the user in planning their travel request.
In the Python code, you need to use the following tools:

# TOOL CONFIG
{self.tool_config}

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
    
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    
        
        return messages
        
    



def plan_generation(conversation, cache_for_conversation, tokeniser_path):
    generator = PlanLLMGenerator(tokeniser_path)
    plan = generator.generate_plan(conversation, cache_for_conversation)
    return plan

def plan_generation_zero_shot(conversation, cache_for_conversation, tokeniser_path):
    generator = PlanLLMGenerator(tokeniser_path)
    plan = generator.generate_plan_zero_shot(conversation, cache_for_conversation)
    return plan

def make_reasoning_prompt(conversation, cache_for_conversation, tokeniser_path):
    # generator = PlanLLMGenerator(tokeniser_path)
    # prompt = generator.prompt_reasoning(conversation, cache_for_conversation)
    prompt_message = prompt_reasoning_final(conversation, cache_for_conversation)

    return prompt_message

def get_batch_results(prompts,tokeniser_path):
   
    # generator = PlanLLMGenerator(tokeniser_path)
    # ans = generator.client.infer_batch(prompts)
    CLIENT_RETRIES = 3


    from openai import OpenAI
    
    model_id = "gpt-5-mini"
    # if "deepseek" in model_id:
    #     base_url = "https://api.deepseek.com"
    # else:
    #     base_url = "https://api.openai.com/v1/"
    client = OpenAI()
    for attempt in range(CLIENT_RETRIES):
        try:

            response = client.responses.create(model=model_id,input=prompts[0],reasoning={"effort": "low"})
        except Exception as e:
            logging.warning("Error calling OpenAI API:")

    #         time.sleep(61)
    # from google import genai
    # from google.genai import types
    
    # # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    # client = genai.Client()
    # for i in range(3):
    #     try:
        
    #         response = client.models.generate_content(
    #             model="gemini-2.5-pro",
    #             contents=prompts[0],
    #             config=types.GenerateContentConfig(
    #                 thinking_config=types.ThinkingConfig(thinking_budget=-1)
    #                 # Turn off thinking:
    #                 # thinking_config=types.ThinkingConfig(thinking_budget=0)
    #                 # Turn on dynamic thinking:
    #                 # thinking_config=types.ThinkingConfig(thinking_budget=-1)
    #             ),
    #         )
    #         break
    #     except Exception as e:
    #         logging.warning("Error calling geimini API:")
    #         time.sleep(61)

    
    
    return response

# if __name__ == "__main__":
#     conversation = """
# [{'assistant': ' Welcome! What brings you here today?'}, {'user': ' I need help with flights and hotels for a solo trip from Detroit to Indianapolis.'}, {'assistant': " What's your preferred flight class?"}, {'user': " I'm looking at economy."}, {'assistant': ' And what are your travel dates?'}, {'user': " I'm flexible, but I'd like to travel around May 18, 2025."}, {'assistant': ' Are you looking for a return flight as well?'}, {'user': ' yeah on May 22, 2025'}, {'assistant': ' Do you want me to give you some restaurant recommendations?'}, {'user': ' yeah good Chinese near hotel would be great. Also make sure the hotel has a pool! I swim every day'}]
# """

# cache_for_conversation = """
# {'flights': 'Flight search results from Detroit to Indianapolis, departing on date(s) [2025-05-18]. flight classes: [economy], max number of layover(s): 1, max layover 1 duration: 60 minutes.', 'return_flights': 'Flight search results from Indianapolis to Detroit, departing on date(s) [2025-05-22]. flight classes: [economy], max number of layover(s): 1, max layover 1 duration: 60 minutes.', 'hotels': 'Hotel search results in Indianapolis from check-in date(s) [2025-05-18] to check-out date(s) [2025-05-22].\nThere are 13 hotel(s) that matched this query!'}
# """
# print(make_reasoning_prompt(conversation, cache_for_conversation,"/home/jovyan/llm-experiments-no-cache/model_zoo/simplescaling_s1.1-32B"))