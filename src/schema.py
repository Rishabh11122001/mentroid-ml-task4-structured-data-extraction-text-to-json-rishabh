"""Strict syntax and schema checks; these do not prove factual correctness."""
import json
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Person(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    name: str | None
    age: int | None = Field(ge=0, le=130)
    profession: str | None

    @field_validator("name", "profession")
    @classmethod
    def nonblank(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Use null for missing values, not an empty string")
        return value

def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result

def reject_constant(value):
    raise ValueError(f"Non-standard JSON constant: {value}")

def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_keys, parse_constant=reject_constant)

def validate_output(raw):
    return Person.model_validate(parse_json(raw))
