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

import ast
from decimal import Decimal
from typing import List

from numpy import float32
from pydantic import (BaseModel, ConfigDict, FieldValidationInfo,
                      field_validator)


class Toy(BaseModel):
    product_id: str
    product_name: str
    description: str
    list_price: Decimal


class Embedding(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    product_id: str
    content: str
    embedding: List[float32]

    @field_validator("embedding", mode="before")
    def validate(cls, v):
        if type(v) == str:
            v = ast.literal_eval(v)
            v = [float32(f) for f in v]
        return v
