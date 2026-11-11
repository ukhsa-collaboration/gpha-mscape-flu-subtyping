import json
import sys
from pathlib import Path

# easiest for this repo if bin is treated as importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))

from summarise_flu_mapping import (
    create_analysis_fields,
    make_pipeline_command,
    make_pipeline_dict,
)


def test_make_pipeline_command_contains_expected_steps():
    command = make_pipeline_command()

    assert isinstance(command, str)
    assert "minimap2" in command
    assert "summarise_flu_mapping.py" in command
    assert "quarto render" in command
    assert "\n" in command


def test_make_pipeline_dict_parses_pipeline_info():
    pipeline_info = "gpha-mscape-flu-subtyping,1.0.0,https://github.com/UKHSA-Internal/mscape-flusubtyping"
    parsed = make_pipeline_dict(pipeline_info)

    assert parsed == {
        "name": "gpha-mscape-flu-subtyping",
        "version": "1.0.0",
        "homePage": "https://github.com/UKHSA-Internal/mscape-flusubtyping",
    }


def test_create_analysis_fields_sets_pipeline_command(monkeypatch):
    # avoid calling Onyx
    monkeypatch.setattr(
        "summarise_flu_mapping.oa.get_data_and_versions_from_onyx",
        lambda **kwargs: ({}, [], 0),
    )

    summary = {
        "climb_id": "C-1234",
        "subtype_call": "H1N1",
        "hacall": "Seasonal",
        "nacall": "Seasonal",
        "ha_reads": 10,
        "na_reads": 8,
        "hacoverage": 0.99,
        "nacoverage": 0.92,
        "clade_call": "Clade call possible",
        "res_conf": "High",
    }

    pipeline_info = {
        "name": "gpha-mscape-flu-subtyping",
        "version": "1.0.0",
        "homePage": "https://github.com/UKHSA-Internal/mscape-flusubtyping",
    }

    analysis, exit_code = create_analysis_fields(
        summary=summary,
        server="devscape",
        pipeline_info=pipeline_info,
        orange_box_version="unknown",
    )

    assert exit_code == 0
    assert hasattr(analysis, "pipeline_command")
    assert isinstance(analysis.pipeline_command, str)
    assert "minimap2" in analysis.pipeline_command
    assert "summarise_flu_mapping.py" in analysis.pipeline_command
    assert "quarto render" in analysis.pipeline_command


def test_pipeline_command_is_written_to_json(tmp_path, monkeypatch):
    # avoid calls to Onyx
    monkeypatch.setattr(
        "summarise_flu_mapping.oa.get_data_and_versions_from_onyx",
        lambda **kwargs: ({}, [], 0),
    )

    summary = {
        "climb_id": "C-1234",
        "subtype_call": "H1N1",
        "hacall": "Seasonal",
        "nacall": "Seasonal",
        "ha_reads": 10,
        "na_reads": 8,
        "hacoverage": 0.99,
        "nacoverage": 0.92,
        "clade_call": "Clade call possible",
        "res_conf": "High",
    }

    pipeline_info = {
        "name": "gpha-mscape-flu-subtyping",
        "version": "1.0.0",
        "homePage": "https://github.com/UKHSA-Internal/mscape-flusubtyping",
    }

    analysis, exit_code = create_analysis_fields(
        summary=summary,
        server="devscape",
        pipeline_info=pipeline_info,
        orange_box_version="unknown",
    )
    assert exit_code == 0

    out = tmp_path / "analysis.json"
    analysis.write_analysis_to_json(out)

    payload = json.loads(out.read_text())
    assert isinstance(payload["pipeline_command"], str)
    assert "minimap2" in payload["pipeline_command"]
    assert "summarise_flu_mapping.py" in payload["pipeline_command"]
    assert "quarto render" in payload["pipeline_command"]