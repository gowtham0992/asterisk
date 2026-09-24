"""Declared evaluation purpose, never inferred or certified by the model."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class EvaluationIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: Literal["unseen_entities", "future_observations", "new_sites", "other"]
    unit: str = Field(default="", max_length=120)

    @model_validator(mode="after")
    def validate_unit(self):
        self.unit = self.unit.strip()
        if self.target == "unseen_entities" and not self.unit:
            raise ValueError("Name the generating unit, for example patients, speakers or specimens.")
        return self

def supported(value):
    if value is None:
        return None
    intent = EvaluationIntent.model_validate(value).model_dump()
    if intent["target"] != "unseen_entities":
        raise ValueError("This check supports separation of recorded entity identities. It cannot establish generalization to future observations, new sites, or another task. Choose a suitable evaluation method before proceeding.")
    return intent

def describe(value):
    if not value:
        return "Intended evaluation was not recorded. No purpose is inferred from this historical receipt."
    intent = supported(value)
    return ("Intended evaluation: unseen " + intent["unit"] + ". The check measures separation of exact recorded identities under your confirmed column meaning. "
            "It does not establish predictive performance, future-time generalization, or generalization to new sites. Human confirmation records an assumption, not independent semantic validation.")
