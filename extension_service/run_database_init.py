# Copyright 2023 Google LLC
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
from typing import List

import datastore
import models
from app import parse_config


async def main() -> None:
    airports: List[models.Airport] = []
    with open("../data/airport_dataset.csv", "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        airports = [models.Airport.model_validate(line) for line in reader]
    flights: List[models.Flight] = []
    with open("../data/flights_dataset.csv", "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        flights = [models.Flight.model_validate(line) for line in reader]

    cfg = parse_config("config.yml")
    ds = await datastore.create(cfg.datastore)
<<<<<<< HEAD
    await ds.initialize_data(airports, flights)
=======
    await ds.initialize_data(toys, embeddings, airports, flights, )
>>>>>>> 29a3384 (Merged with main)
    await ds.close()


if __name__ == "__main__":
    asyncio.run(main())
