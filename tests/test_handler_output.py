from __future__ import annotations

from decimal import Decimal

import pytest
from keel.handlers import GeneratedFileRef, HandlerOutput, ModelUsage
from pydantic import ValidationError


def test_handler_output_defaults_are_empty_and_jsonable():
    output = HandlerOutput()

    assert output.summary is None
    assert output.generated_files == []
    assert output.warnings == []
    assert output.next_step is None
    assert output.tokens_in == 0
    assert output.tokens_out == 0
    assert output.model_usage == []
    assert output.output_digest is None
    assert output.metadata == {}
    assert output.model_dump(mode="json") == {
        "summary": None,
        "generated_files": [],
        "warnings": [],
        "next_step": None,
        "tokens_in": 0,
        "tokens_out": 0,
        "model_usage": [],
        "output_digest": None,
        "metadata": {},
    }


def test_handler_output_accepts_generated_files_and_usage():
    output = HandlerOutput(
        summary="done",
        generated_files=[
            GeneratedFileRef(
                path="jobs/report.md",
                size=123,
                modified_at="2026-06-10T12:34:56Z",
            )
        ],
        warnings=["check manually"],
        next_step="open report",
        tokens_in=10,
        tokens_out=20,
        model_usage=[
            ModelUsage(
                model="openrouter/test",
                tokens_in=10,
                tokens_out=20,
                provider_cost_cny=Decimal("0.12"),
                charged_cost_cny=Decimal("0.15"),
            )
        ],
        output_digest="sha256:abc",
        metadata={"runner": "review_opinion"},
    )

    dumped = output.model_dump(mode="json")
    assert dumped["generated_files"] == [
        {
            "path": "jobs/report.md",
            "size": 123,
            "content_hash": None,
            "modified_at": "2026-06-10T12:34:56Z",
        }
    ]
    assert dumped["model_usage"][0]["provider_cost_cny"] == "0.12"
    assert dumped["metadata"] == {"runner": "review_opinion"}


def test_handler_output_accepts_generated_file_modified_at_from_payload():
    output = HandlerOutput.model_validate(
        {
            "generated_files": [
                {
                    "path": "jobs/report.md",
                    "size": 123,
                    "content_hash": "sha256:abc",
                    "modified_at": "2026-06-10T12:34:56Z",
                }
            ]
        }
    )

    assert output.generated_files == [
        GeneratedFileRef(
            path="jobs/report.md",
            size=123,
            content_hash="sha256:abc",
            modified_at="2026-06-10T12:34:56Z",
        )
    ]


def test_generated_file_ref_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        GeneratedFileRef.model_validate(
            {"path": "jobs/report.md", "modified_at": "2026-06-10T12:34:56Z", "extra": True}
        )


def test_handler_output_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        HandlerOutput.model_validate({"summary": "x", "unexpected": True})
