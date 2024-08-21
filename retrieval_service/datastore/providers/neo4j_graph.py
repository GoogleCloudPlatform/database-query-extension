# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import csv
from typing import Literal, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase
from pydantic import BaseModel

import models

from .. import datastore

NEO4J_IDENTIFIER = "neo4j"


class AuthConfig(BaseModel):
    username: str
    password: str


class Config(BaseModel, datastore.AbstractConfig):
    kind: Literal["neo4j"]
    uri: str
    auth: AuthConfig


class Client(datastore.Client[Config]):
    __driver: AsyncDriver

    @datastore.classproperty
    def kind(cls):
        return NEO4J_IDENTIFIER

    def __init__(self, driver):
        self.__driver = driver

    @property
    def driver(self):
        return self.__driver

    @classmethod
    async def create(cls, config: Config) -> "Client":
        return cls(
            AsyncGraphDatabase.driver(
                config.uri, auth=(config.auth.username, config.auth.password)
            )
        )

    async def initialize_data(
        self,
        airports: list[models.Airport],
        amenities: list[models.Amenity],
        flights: list[models.Flight],
        policies: list[models.Policy],
    ) -> None:
        async def delete_graph(tx):
            await tx.run("MATCH (n) DETACH DELETE n")

        async def delete_vector_index(tx):
            # Delete amenity vector index
            await tx.run("DROP INDEX amenity_embedding IF EXISTS")

        async def create_amenity_nodes(tx, amenities):
            for amenity in amenities:
                # Create Amenity node
                await tx.run(
                    """
                    CREATE (a:Amenity {id: $id, name: $name, description: $description, location: $location, terminal: $terminal, category: $category, hour: $hour, embedding: $embedding})
                    """,
                    id=amenity.id,
                    name=amenity.name,
                    description=amenity.description,
                    location=amenity.location,
                    terminal=amenity.terminal,
                    category=amenity.category,
                    hour=amenity.hour,
                    embedding=amenity.embedding,
                )

                # Create Category node
                # MERGE prevents duplicate nodes by first checking if they already exist
                await tx.run(
                    """
                    MERGE (c:Category {name: $category})
                    """,
                    category=amenity.category,
                )

        async def create_amenity_relationships(tx, amenities):
            for amenity in amenities:
                # Create BELONGS_TO relationship
                # MERGE prevents duplicate relationships by first checking if they already exist
                await tx.run(
                    """
                    MATCH (a:Amenity {id: $id}), (c:Category {name: $category})
                    MERGE (a)-[:BELONGS_TO]->(c)
                    """,
                    id=amenity.id,
                    category=amenity.category,
                )

            # Create relationships from CSV
            # Create SIMILAR_TO relationship
            csv_file_path = "../data/relationships/amenity_relationships.csv"

            with open(csv_file_path, "r") as file:
                reader = csv.DictReader(file, delimiter=",")
                for row in reader:
                    src_name = row["src_id"]
                    rel_type = row["rel_type"]
                    tgt_name = row["tgt_id"]

                    # Generate and run the Cypher query
                    # Case-insensitive and apostrophes-insensitive match
                    await tx.run(
                        f"""
                        MATCH (a:Amenity) WHERE toLower(a.name) = toLower("{src_name}")
                        MATCH (b:Amenity) WHERE toLower(b.name) = toLower("{tgt_name}")
                        MERGE (a)-[:{rel_type}]->(b)
                        """,
                    )

        async def create_vector_index(tx):
            # Create amenity vector index
            # Cosine and Euclidean are the only supported similarity functions
            # Cosine is the most similar to Dot-Product default function
            await tx.run(
                """
                CREATE VECTOR INDEX amenity_embedding IF NOT EXISTS
                FOR (a:Amenity)
                ON a.embedding
                OPTIONS {indexConfig: {
                `vector.dimensions`: 768,
                `vector.similarity_function`: 'cosine'
                }}
                """
            )

        async with self.__driver.session() as session:
            # Delete all existing nodes and relationships
            await session.execute_write(delete_graph)

            # Delete all indexes
            await session.execute_write(delete_vector_index)

            # Create nodes
            await asyncio.gather(
                # Create amenity nodes
                session.execute_write(create_amenity_nodes, amenities)
            )

            # Create relationships
            await asyncio.gather(
                # Create amenity relationships
                session.execute_write(create_amenity_relationships, amenities)
            )

            # Create vector index
            await session.execute_write(create_vector_index)

    async def export_data(self) -> tuple[
        list[models.Airport],
        list[models.Amenity],
        list[models.Flight],
        list[models.Policy],
    ]:
        raise NotImplementedError("This client does not support airports.")

    async def get_airport_by_id(self, id: int) -> Optional[models.Airport]:
        raise NotImplementedError("This client does not support airports.")

    async def get_airport_by_iata(self, iata: str) -> Optional[models.Airport]:
        raise NotImplementedError("This client does not support airports.")

    async def search_airports(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[models.Airport]:
        raise NotImplementedError("This client does not support airports.")

    async def get_amenity(self, id: int) -> Optional[models.Amenity]:
        async with self.__driver.session() as session:
            # Specify return fields so embedding field wont be included in it
            result = await session.run(
                """
                MATCH (amenity: Amenity {id: $id})
                RETURN amenity.id AS id,
                    amenity.name AS name,
                    amenity.description AS description,
                    amenity.location AS location,
                    amenity.terminal AS terminal,
                    amenity.category AS category,
                    amenity.hour AS hour
                """,
                id=id,
            )
            record = await result.single()

            if not record:
                return None

            return models.Amenity(**record)

    async def amenities_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[dict]:
        async with self.__driver.session() as session:
            # OPTIONAL ensures that all similar amenities are returned even if they lack a SIMILAR_TO relationship
            # Limit retrieval to 2 target nodes related to the source node, linked by SIMILAR_TO relationship
            # Lower case relationship due to graph generator output
            result = await session.run(
                """
                CALL db.index.vector.queryNodes('amenity_embedding', $top_k, $query_embedding)
                YIELD node AS sourceAmenity
                OPTIONAL MATCH (sourceAmenity)-[r:Similar_to]-(targetAmenity)
                RETURN sourceAmenity.name AS source_name,
                        sourceAmenity.description AS source_description,
                        sourceAmenity.location AS source_location,
                        sourceAmenity.terminal AS source_terminal,
                        sourceAmenity.category AS source_category,
                        sourceAmenity.hour AS source_hour,
                        type(r) AS relationship_type,
                        targetAmenity.name AS target_name,
                        targetAmenity.description AS target_description,
                        targetAmenity.location AS target_location,
                        targetAmenity.terminal AS target_terminal,
                        targetAmenity.category AS target_category,
                        targetAmenity.hour AS target_hour
                LIMIT 2
                """,
                query_embedding=query_embedding,
                top_k=top_k,
            )

            amenities = await result.data()

            return amenities

    async def get_flight(self, flight_id: int) -> Optional[models.Flight]:
        raise NotImplementedError("This client does not support flights.")

    async def search_flights_by_number(
        self, airline: str, flight_number: str
    ) -> list[models.Flight]:
        raise NotImplementedError("This client does not support flights.")

    async def search_flights_by_airports(
        self,
        date,
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
    ) -> list[models.Flight]:
        raise NotImplementedError("This client does not support flights.")

    async def validate_ticket(
        self,
        airline: str,
        flight_number: str,
        departure_airport: str,
        departure_time: str,
    ) -> Optional[models.Flight]:
        raise NotImplementedError("This client does not support tickets.")

    async def insert_ticket(
        self,
        user_id: str,
        user_name: str,
        user_email: str,
        airline: str,
        flight_number: str,
        departure_airport: str,
        arrival_airport: str,
        departure_time: str,
        arrival_time: str,
    ):
        raise NotImplementedError("This client does not support tickets.")

    async def list_tickets(self, user_id: str) -> list[models.Ticket]:
        raise NotImplementedError("This client does not support tickets.")

    async def policies_search(
        self, query_embedding: list[float], similarity_threshold: float, top_k: int
    ) -> list[str]:
        raise NotImplementedError("This client does not support policies.")

    async def close(self):
        await self.__driver.close()
