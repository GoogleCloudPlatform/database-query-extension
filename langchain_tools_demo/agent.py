# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import Optional

import google.auth.transport.requests
import google.oauth2.id_token

import requests
from langchain.agents import AgentType, initialize_agent

# from langchain.agents.mrkl.base import ZeroShotAgent
from langchain.chat_models.vertexai import ChatVertexAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import StructuredTool, Tool
from pydantic.v1 import BaseModel, Field

DEBUG = bool(os.getenv("DEBUG", default=False))
BASE_URL = os.getenv("BASE_URL", default="http://127.0.0.1:8080")


def init_agent(history):
    """Load an agent executor with tools and LLM"""
    print("Initializing agent..")
    llm = ChatVertexAI(max_output_tokens=512, verbose=DEBUG)
    memory = ConversationBufferMemory(
        memory_key="chat_history",
    )
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=DEBUG,
        memory=memory,
        handle_parsing_errors=True,
    )
    agent.agent.llm_chain.verbose = DEBUG
    return agent


def get_id_token():
    auth_req = google.auth.transport.requests.Request()
    target_audience = BASE_URL

    return google.oauth2.id_token.fetch_id_token(auth_req, target_audience)


def get_flight(id: int):
    response = requests.get(
        f"{BASE_URL}/flights",
        params={"id": id},
        headers={"Authorization": f"Bearer {get_id_token()}"},
    )

    if response.status_code != 200:
        return f"Error trying to find flight: {response.text}"

    return response.json()


def list_flights(departure_airport: str, arrival_airport: str, date: str):
    params = {
        "departure_airport": departure_airport,
        "arrival_airport": arrival_airport,
        "date": date,
    }

    response = requests.get(
        f"{BASE_URL}/flights/search",
        params,
        headers={"Authorization": f"Bearer {get_id_token()}"},
    )
    if response.status_code != 200:
        return f"Error searching flights: {response.text}"

    return response.json()


def get_amenity(id: int):
    response = requests.get(
        f"{BASE_URL}/amenities",
        params={"id": id},
        headers={"Authorization": f"Bearer {get_id_token()}"},
    )

    if response.status_code != 200:
        return f"Error trying to find amenity: {response.text}"

    return response.json()


def search_amenities(query: str):
    params = {"top_k": "5", "query": query}

    response = requests.get(
        f"{BASE_URL}/amenities/search",
        params,
        headers={"Authorization": f"Bearer {get_id_token()}"},
    )
    if response.status_code != 200:
        return f"Error searching amenities: {response.text}"

    return response.json()


def get_airport(id: int):
    response = requests.get(
        f"{BASE_URL}/airports",
        params={"id": id},
        headers={"Authorization": f"Bearer {get_id_token()}"},
    )

    if response.status_code != 200:
        return f"Error trying to find airport: {response.text}"

    return response.json()


def search_airports(query: str):
    params = {"top_k": "5", "query": query}

    response = requests.get(
        f"{BASE_URL}/airports/semantic_lookup",
        params,
        headers={"Authorization": f"Bearer {get_id_token()}"},
    )
    if response.status_code != 200:
        return f"Error searching airports: {response.text}"

    return response.json()


class IdInput(BaseModel):
    id: int = Field(description="Unique identifier")


class QueryInput(BaseModel):
    query: str = Field(description="Search query")


class ListFlights(BaseModel):
    departure_airport: Optional[str] = Field(
        description="Departure airport 3-letter code"
    )
    arrival_airport: Optional[str] = Field(description="Arrival airport 3-letter code")
    date: str = Field(description="Date of flight departure", default="today")


tools = [
    # Tool.from_function(
    #     name="get_flight",  # Name must be unique for tool set
    #     func=get_flight,
    #     description="Use this tool to get info for a specific flight. Takes an id and returns info on the flight.",
    #     args_schema=IdInput,
    # ),
    # StructuredTool.from_function(
    #     name="list_flights",
    #     func=list_flights,
    #     description="Use this tool to list all flights matching search criteria.",
    #     args_schema=ListFlights,
    # ),
    Tool.from_function(
        name="get_amenity",
        func=get_amenity,
        description="Use this tool to get info for a specific airport amenity. Takes an id and returns info on the amenity. Use the id from the search_amenities tool.",
        # args_schema=IdInput,
    ),
    Tool.from_function(
        name="search_amenities",
        func=search_amenities,
        description="Use this tool to recommended airport amenities at SFO. Returns several amenities that are related to the query. Only recommend amenities that are returned by this query.",
        args_schema=QueryInput,
    ),
    # Tool.from_function(
    #     name="get_airport",
    #     func=get_airport,
    #     description="Use this tool to get info for a specific airport. Takes an id and returns info on the airport.",
    #     args_schema=IdInput,
    # ),
    # Tool.from_function(
    #     name="search_airports",
    #     func=search_airports,
    #     description="Use this tool to search for airports.",
    #     args_schema=QueryInput,
    # ),
]
