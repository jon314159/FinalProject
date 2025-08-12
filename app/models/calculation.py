# app/models/calculation.py
"""
Calculation Models Module

This module defines the database models for calculations using SQLAlchemy ORM.
It demonstrates several advanced patterns:

1. Polymorphic inheritance - One table for all calculation types
2. Factory pattern - Using create() to instantiate the right calculation subclass
3. Strategy pattern - Each calculation type implements its own business logic
4. Single Responsibility Principle - Each calculation type does one thing

These models are designed for a calculator application that supports
basic mathematical operations: addition, subtraction, multiplication, and division.
"""

import uuid
from typing import List

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declared_attr

from app.database import Base


class AbstractCalculation:
    """
    Abstract base class for calculations.

    Uses single-table inheritance and common fields.
    """

    @declared_attr
    def __tablename__(cls):
        return "calculations"

    @declared_attr
    def id(cls):
        return Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        )

    @declared_attr
    def user_id(cls):
        return Column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

    @declared_attr
    def type(cls):
        return Column(
            String(50),
            nullable=False,
            index=True,
        )

    @declared_attr
    def inputs(cls):
        return Column(JSON, nullable=False)

    @declared_attr
    def result(cls):
        return Column(Float, nullable=True)

    @declared_attr
    def created_at(cls):
        """
        UTC timestamp when the calculation was created.
        Database clock is the source of truth.
        """
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls):
        """
        UTC timestamp when the calculation was last updated.
        Automatically updated by the database.
        """
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )

    @declared_attr
    def user(cls):
        return relationship("User", back_populates="calculations")

    @classmethod
    def create(cls, calculation_type: str, user_id: uuid.UUID, inputs: List[float]) -> "Calculation":
        calculation_classes = {
            "addition": Addition,
            "subtraction": Subtraction,
            "multiplication": Multiplication,
            "division": Division,
            "modulus": Modulus,
        }
        calculation_class = calculation_classes.get(calculation_type.lower())
        if not calculation_class:
            raise ValueError(f"Unsupported calculation type: {calculation_type}")
        return calculation_class(user_id=user_id, inputs=inputs)

    def get_result(self) -> float:
        raise NotImplementedError

    def __repr__(self):
        return f"<Calculation(type={self.type}, inputs={self.inputs})>"


class Calculation(Base, AbstractCalculation):
    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "calculation",
    }


class Addition(Calculation):
    __mapper_args__ = {"polymorphic_identity": "addition"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        return sum(self.inputs)


class Subtraction(Calculation):
    __mapper_args__ = {"polymorphic_identity": "subtraction"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = self.inputs[0]
        for value in self.inputs[1:]:
            result -= value
        return result


class Multiplication(Calculation):
    __mapper_args__ = {"polymorphic_identity": "multiplication"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = 1
        for value in self.inputs:
            result *= value
        return result


class Division(Calculation):
    __mapper_args__ = {"polymorphic_identity": "division"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = self.inputs[0]
        for value in self.inputs[1:]:
            if value == 0:
                raise ValueError("Cannot divide by zero.")
            result /= value
        return result


class Modulus(Calculation):
    """
    Modulus calculation subclass.
    """
    __mapper_args__ = {"polymorphic_identity": "modulus"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = self.inputs[0]
        for value in self.inputs[1:]:
            result %= value
        return result
