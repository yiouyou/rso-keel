from __future__ import annotations

import pytest
from pydantic import ValidationError

from keel.lab import ExperimentCardDeck


def _card(**overrides):
    data = {
        "card_id": "exp-1",
        "title": "Validate public-data signal",
        "modality": "public_data",
        "purpose": "Check whether the proposed association appears in an independent cohort.",
        "hypothesis": "If the association is real, the independent cohort should show the same direction.",
        "materials": [{"category": "dataset", "description": "Independent public cohort"}],
        "expected_results": [
            {
                "condition": "positive",
                "observation": "Same-direction association is observed.",
                "interpretation": "The opportunity is worth deeper review.",
            }
        ],
        "controls": ["Compare against unrelated endpoint"],
        "decision_rules": [
            {
                "if_result": "No same-direction signal",
                "then_decision": "stop",
                "rationale": "The cheap falsification check failed.",
            }
        ],
        "evidence_links": [
            {"source_id": "paper:1", "claim": "Mechanistic plausibility", "relation": "motivates"}
        ],
    }
    data.update(overrides)
    return data


def test_experiment_card_deck_accepts_reviewable_card():
    deck = ExperimentCardDeck.model_validate(
        {"objective": "Find cheap validation step", "cards": [_card()]}
    )

    assert deck.requires_human_review is True
    assert deck.cards[0].card_id == "exp-1"
    assert deck.cards[0].materials[0].category == "dataset"


def test_wet_lab_card_requires_safety_flags():
    with pytest.raises(ValidationError, match="safety_ethics_flags"):
        ExperimentCardDeck.model_validate(
            {
                "objective": "Validate in vitro",
                "cards": [_card(modality="wet_lab", materials=[])],
            }
        )


def test_deck_rejects_more_than_five_cards():
    with pytest.raises(ValidationError, match="at most 5"):
        ExperimentCardDeck.model_validate(
            {"objective": "Too many", "cards": [_card(card_id=f"exp-{i}") for i in range(6)]}
        )


def test_schema_rejects_uncontrolled_protocol_steps():
    card = _card()
    card["protocol_steps"] = ["do not encode SOPs here"]

    with pytest.raises(ValidationError, match="Extra inputs"):
        ExperimentCardDeck.model_validate({"objective": "No SOP", "cards": [card]})
