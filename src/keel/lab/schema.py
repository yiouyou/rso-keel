"""Schemas for lab-in-loop experiment proposal cards.

These models describe reviewable experiment suggestions. They intentionally do
not encode executable SOP steps, dosages, timings, or instrument settings.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ExperimentModality = Literal["wet_lab", "dry_lab", "computational", "public_data"]
MaterialCategory = Literal[
    "sample",
    "assay",
    "dataset",
    "software",
    "instrument",
    "cell_line",
    "reagent_class",
    "other",
]


class EvidenceLink(BaseModel):
    """Evidence or context supporting the proposed experiment."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    claim: str
    relation: Literal["supports", "contradicts", "motivates", "risk"] = "supports"


class MaterialRequirement(BaseModel):
    """High-level material need, not a step-by-step protocol item."""

    model_config = ConfigDict(extra="forbid")

    category: MaterialCategory
    description: str
    required: bool = True


class ExpectedResult(BaseModel):
    """Expected observation and what it would mean."""

    model_config = ConfigDict(extra="forbid")

    condition: Literal["positive", "negative", "ambiguous"]
    observation: str
    interpretation: str


class DecisionRule(BaseModel):
    """Decision logic for whether to deepen, revise, or stop."""

    model_config = ConfigDict(extra="forbid")

    if_result: str
    then_decision: Literal["deepen", "revise", "stop", "seek_expert_review"]
    rationale: str


class ExperimentCard(BaseModel):
    """A reviewable experiment recommendation card."""

    model_config = ConfigDict(extra="forbid")

    card_id: str
    title: str
    modality: ExperimentModality
    purpose: str
    hypothesis: str
    materials: list[MaterialRequirement] = Field(default_factory=list)
    expected_results: list[ExpectedResult]
    controls: list[str] = Field(default_factory=list)
    decision_rules: list[DecisionRule]
    safety_ethics_flags: list[str] = Field(default_factory=list)
    evidence_links: list[EvidenceLink] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    limitations: list[str] = Field(default_factory=list)

    @field_validator("card_id", "title", "purpose", "hypothesis")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("field must be non-empty")
        return stripped

    @model_validator(mode="after")
    def _reviewable_not_executable(self) -> "ExperimentCard":
        if not self.expected_results:
            raise ValueError("expected_results must contain at least one item")
        if not self.decision_rules:
            raise ValueError("decision_rules must contain at least one item")
        if self.modality == "wet_lab" and not self.safety_ethics_flags:
            raise ValueError("wet_lab cards must include safety_ethics_flags")
        return self


class ExperimentCardDeck(BaseModel):
    """A bounded set of experiment cards emitted by one workflow."""

    model_config = ConfigDict(extra="forbid")

    objective: str
    cards: list[ExperimentCard]
    requires_human_review: Literal[True] = True

    @model_validator(mode="after")
    def _bounded_cards(self) -> "ExperimentCardDeck":
        if not self.cards:
            raise ValueError("cards must contain at least one experiment card")
        if len(self.cards) > 5:
            raise ValueError("cards must contain at most 5 experiment cards")
        return self
