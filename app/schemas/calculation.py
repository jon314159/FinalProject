"""
Calculation Schemas Module
"""

from enum import Enum
import math
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class CalculationType(str, Enum):
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"
    MODULUS = "modulus"

class CalculationBase(BaseModel):
    type: CalculationType = Field(
        ...,
        description="Type of calculation (addition, subtraction, multiplication, division, modulus)",
        examples=["addition"],
    )
    inputs: List[float] = Field(
        ...,
        description="List of numeric inputs for the calculation",
        examples=[[10.5, 3, 2]],
        min_length=2,  # Pydantic v2 uses min_length for lists
    )

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")
        return v.lower()

    @field_validator("inputs", mode="before")
    @classmethod
    def check_inputs_is_list(cls, v):
        if not isinstance(v, list):
            raise ValueError("Input should be a valid list")
        if any(isinstance(value, bool) for value in v):
            raise ValueError("Inputs must contain only numbers")
        return v

    @model_validator(mode="after")
    def validate_inputs(self) -> "CalculationBase":
        if len(self.inputs) < 2:
            raise ValueError("At least two numbers are required for calculation")
        if any(not math.isfinite(value) for value in self.inputs):
            raise ValueError("Inputs must contain only finite numbers")
        if self.type in (CalculationType.DIVISION, CalculationType.MODULUS):
            if any(x == 0 for x in self.inputs[1:]):
                operation = "divide" if self.type == CalculationType.DIVISION else "calculate modulus"
                raise ValueError(f"Cannot {operation} by zero")
        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {"type": "addition", "inputs": [10.5, 3, 2]},
                {"type": "division", "inputs": [100, 2]},
            ]
        },
    )

class CalculationCreate(CalculationBase):
    user_id: UUID = Field(
        ...,
        description="UUID of the user who owns this calculation",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "addition",
                    "inputs": [10.5, 3, 2],
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                }
            ]
        }
    )

class CalculationUpdate(BaseModel):
    inputs: Optional[List[float]] = Field(
        None,
        description="Updated list of numeric inputs for the calculation",
        examples=[[42, 7]],
        min_length=2,
    )

    @field_validator("inputs", mode="before")
    @classmethod
    def check_inputs(cls, value):
        if value is not None and not isinstance(value, list):
            raise ValueError("Input should be a valid list")
        if value is not None and any(isinstance(item, bool) for item in value):
            raise ValueError("Inputs must contain only numbers")
        return value

    @model_validator(mode="after")
    def validate_inputs(self) -> "CalculationUpdate":
        if self.inputs is not None and len(self.inputs) < 2:
            raise ValueError("At least two numbers are required for calculation")
        if self.inputs is not None and any(not math.isfinite(value) for value in self.inputs):
            raise ValueError("Inputs must contain only finite numbers")
        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{"inputs": [42, 7]}]},
    )

class CalculationResponse(CalculationBase):
    id: UUID = Field(
        ...,
        description="Unique UUID of the calculation",
        examples=["123e4567-e89b-12d3-a456-426614174999"],
    )
    user_id: UUID = Field(
        ...,
        description="UUID of the user who owns this calculation",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    created_at: datetime = Field(
        ...,
        description="Time when the calculation was created",
        examples=["2025-01-01T00:00:00"],
    )
    updated_at: datetime = Field(
        ...,
        description="Time when the calculation was last updated",
        examples=["2025-01-01T00:00:00"],
    )
    result: float = Field(
        ...,
        description="Result of the calculation",
        examples=[15.5],
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174999",
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "type": "addition",
                    "inputs": [10.5, 3, 2],
                    "result": 15.5,
                    "created_at": "2025-01-01T00:00:00",
                    "updated_at": "2025-01-01T00:00:00",
                }
            ]
        },
    )
