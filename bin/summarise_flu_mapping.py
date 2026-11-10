#!/usr/bin/env python3
"""Summarise Minimap2 flu mapping results and create an Onyx analysis JSON."""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

import pandas as pd
from onyx_analysis_helper import onyx_analysis_helper_functions as oa

MAPPING_COLUMNS = [
    "query_name",
    "query_len",
    "query_start_coord",
    "query_end_coord",
    "strand",
    "target_name",
    "target_length",
    "target_start",
    "target_end",
    "num_base_mapped",
    "num_bases_gaps_mapped",
    "mapping_quality",
    "x1",
    "x2",
    "x3",
    "x4",
    "x5",
    "x6",
]

SEGMENT_LENGTHS = {
    "PB2": 2341,
    "PB1": 2341,
    "PA": 2233,
    "HA": 1778,
    "MP": 1565,
    "NA": 1413,
    "NP": 1027,
    "NS": 890,
}


def read_mapping_table(mapped_tab: Path) -> pd.DataFrame:
    """Read the headerless Minimap2 table."""
    if not mapped_tab.is_file():
        raise FileNotFoundError(f"Mapping file not found: {mapped_tab}")

    try:
        table = pd.read_csv(mapped_tab, sep="\t", header=None)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=MAPPING_COLUMNS)

    if table.empty:
        return pd.DataFrame(columns=MAPPING_COLUMNS)

    if table.shape[1] != len(MAPPING_COLUMNS):
        raise ValueError(
            f"Expected {len(MAPPING_COLUMNS)} columns in {mapped_tab}, "
            f"found {table.shape[1]}"
        )

    table.columns = MAPPING_COLUMNS
    return table


def prepare_mapping_hits(mapping: pd.DataFrame) -> pd.DataFrame:
    """Parse target names and retain the best hit for each query."""
    mapping = mapping.copy()

    if mapping.empty:
        for column in (
            "target_segment",
            "target_isolate",
            "target_subtype",
            "hit_Htype",
            "hit_Ntype",
        ):
            mapping[column] = pd.Series(dtype="object")
        return mapping

    # Expected target_name structure, matching the original report:
    # segment|isolate|A|subtype
    target_fields = mapping["target_name"].astype(str).str.split(
        "|", n=3, expand=True, regex=False
    )
   # print(target_fields)
    if target_fields.shape[1] < 3:
        raise ValueError(
            "Expected target_name values formatted as "
            "'segment|isolate|subtype'"
        )

    mapping["target_segment"] = target_fields[0].fillna("NA")
    mapping["target_isolate"] = target_fields[1]
    mapping["target_subtype"] = target_fields[2]

    # The original report split subtype labels on N, then removed H and A/.
    subtype_fields = mapping["target_subtype"].astype(str).str.split(
        "N", n=1, expand=True, regex=False
    )
    mapping["hit_Htype"] = (
        subtype_fields[0]
        .str.replace("H", "", regex=False)
        .str.replace("A/", "", regex=False)
    )
    if subtype_fields.shape[1] > 1:
        mapping["hit_Ntype"] = subtype_fields[1].str.replace("|", "", regex=False)
    else:
        mapping["hit_Ntype"] = ""

    mapping["num_base_mapped"] = pd.to_numeric(
        mapping["num_base_mapped"], errors="coerce"
    ).fillna(0)
    mapping["mapping_quality"] = pd.to_numeric(
        mapping["mapping_quality"], errors="coerce"
    ).fillna(0)

    return (
        mapping.sort_values(
            ["query_name", "mapping_quality", "num_base_mapped"],
            kind="stable",
        )
        .drop_duplicates(subset=["query_name"], keep="last")
        .reset_index(drop=True)
    )


def build_segment_table(best_hits: pd.DataFrame) -> pd.DataFrame:
    """Create one summary-table row for each influenza segment."""
    rows = []

    for segment, estimated_length in SEGMENT_LENGTHS.items():
        segment_hits = best_hits[best_hits["target_segment"] == segment]
        read_count = int(segment_hits.shape[0])

        if read_count:
            coverage = float(segment_hits["num_base_mapped"].sum()) / estimated_length
            subtype_coverages = []

            for subtype in sorted(
                segment_hits["target_subtype"].dropna().astype(str).unique()
            ):
                subtype_hits = segment_hits[
                    segment_hits["target_subtype"].astype(str) == subtype
                ]
                subtype_coverage = (
                    float(subtype_hits["num_base_mapped"].sum()) / estimated_length
                )
                subtype_coverages.append(f"{subtype}:{subtype_coverage:.2f}")

            subtype_mapped = ";".join(subtype_coverages)
        else:
            coverage = 0.0
            subtype_mapped = "0"

        rows.append(
            {
                "Num_reads": read_count,
                "Estimated_coverage": round(coverage, 2),
                "Subtype_mapped": subtype_mapped,
                "Segment": segment,
            }
        )

    return pd.DataFrame(rows)


def segment_type_call(
    best_hits: pd.DataFrame,
    segment: str,
) -> tuple[str, str, bool]:
    """Return display call, category, and seasonal flag for HA or NA."""
    rows = best_hits[best_hits["target_segment"] == segment]
    prefix = "H" if segment == "HA" else "N"

    if rows.empty:
        return f"{prefix}-", "No reads detected", False

    field = "hit_Htype" if segment == "HA" else "hit_Ntype"
    subtypes = sorted(
        value.replace("pdm09", "")
        for value in rows[field].dropna().astype(str).unique()
        if value and value.lower() != "nan"
    )
    subtypes = list(set(subtypes))
   # print(subtypes)
    if not subtypes:
        return f"{prefix}-", "No subtype detected", False

    if len(subtypes) > 1:
        return f"{prefix}{';'.join(subtypes)}", "Mixed subtypes detected", False

    subtype = subtypes[0]
   # print(subtype)
    seasonal_subtypes = {"1", "3", "B/Vic"} if segment == "HA" else {
        "1",
        "2",
        "B/Vic",
    }
    is_seasonal = (
        subtype in seasonal_subtypes
        or "pdm09" in subtype.lower()
        or "B/Vic" in subtype
    )

    display_subtype = subtype.replace("pdm09", "").replace("|", "")
   # print(display_subtype)
    call = f"{prefix}{display_subtype}"

    if subtype == "B/Vic":
        call = f"InfB: {segment}-B/Vic"

    if is_seasonal:
        category = "Seasonal"
    else:
        category = f"Non-seasonal influenza {segment} reads detected"

    return call, category, is_seasonal


def confidence_for_read_count(read_count: int) -> str:
    if read_count <= 2:
        return "Low"
    if read_count <= 5:
        return "Medium"
    return "High"


def analyze_mapping(
    mapped_tab: Path,
    climb_id: str,
) -> tuple[pd.DataFrame, dict]:
    """Calculate segment statistics and report-level calls."""
    best_hits = prepare_mapping_hits(read_mapping_table(mapped_tab))
    segment_table = build_segment_table(best_hits)
    segments = segment_table.set_index("Segment")

    ha_call, ha_category, ha_seasonal = segment_type_call(best_hits, "HA")
    na_call, na_category, na_seasonal = segment_type_call(best_hits, "NA")

    ha_reads = int(segments.loc["HA", "Num_reads"])
    na_reads = int(segments.loc["NA", "Num_reads"])
    ha_coverage = float(segments.loc["HA", "Estimated_coverage"])
    na_coverage = float(segments.loc["NA", "Estimated_coverage"])

    confidence = [
        confidence_for_read_count(ha_reads),
        confidence_for_read_count(na_reads),
    ]
    if "Low" in confidence:
        result_confidence = "Low"
    elif "Medium" in confidence:
        result_confidence = "Medium"
    else:
        result_confidence = "High"

    summary = {
        "climb_id": climb_id,
        "subtype_call": f"{ha_call}{na_call}",
        "hacall": ha_category,
        "nacall": na_category,
        "ha_reads": ha_reads,
        "na_reads": na_reads,
        "hacoverage": ha_coverage,
        "nacoverage": na_coverage,
        "clade_call": (
            "Clade call possible"
            if ha_coverage >= 0.9
            else "Coverage too low for clade call"
        ),
        "res_conf": result_confidence,
        "ha_seasonal": ha_seasonal,
        "na_seasonal": na_seasonal,
    }

    return segment_table, summary


def make_pipeline_dict(pipeline_info: str) -> dict:
    """Parse pipeline info formatted as name,version,homepage."""
    parts = pipeline_info.split(",", maxsplit=2)
    if len(parts) != 3 or any(not part.strip() for part in parts):
        raise ValueError(
            "pipeline-info must be formatted as "
            "'pipeline name,version,homepage URL'"
        )

    return {
        "name": parts[0].strip(),
        "version": parts[1].strip(),
        "homePage": parts[2].strip(),
    }


def create_analysis_fields(
    summary: dict,
    server: str,
    pipeline_info: dict,
    orange_box_version: str,
):
    """Build and validate the Onyx analysis object."""
    analysis = oa.OnyxAnalysis()
    analysis.add_analysis_details(
        analysis_name="gpha-mscape-flu-subtyping",
        analysis_description=(
            "This is the flu subtyping pathogen characterisation pipeline"
        ),
    )

    analysis.pipeline_name = pipeline_info["name"]
    analysis.pipeline_version = pipeline_info["version"]
    analysis.pipeline_url = pipeline_info["homePage"]
    analysis.outputs = "No s3 outputs"
    analysis.identifiers = []

    today = datetime.date.today().isoformat()
    analysis.analysis_date = today
  #  analysis.published_date = today

    # Add methods and versions in the helper's expected format
    methods_fail = analysis.add_methods({
        "command": "summarise_flu_mapping.py",
        "analysis_type": "flu_subtyping",
    })

    _, onyx_versions, query_exitcode = oa.get_data_and_versions_from_onyx(
        sample_id=summary["climb_id"],
        server=server,
        fields=["climb_id"],
    )

    versions_fail = False
    if query_exitcode == 0:
        versions_fail = analysis.add_versions_to_methods(
            tool_versions={"orange_box_version": orange_box_version},
            onyx_versions=onyx_versions,
        )

    # The helper expects result_metrics as a dict.
    result_fields = {
        "analysis_date": today,
        "name": "flu_subtyping",
        "details": "Flu subtyping – minimap2/bwa-mem",
        "exit_code": 0,
        "pipeline_status": "success",
        "result": {
            "flu_subtype": summary["subtype_call"],
            "fluHA_category": summary["hacall"],
            "fluNA_category": summary["nacall"],
            "HA_reads": str(summary["ha_reads"]),
            "NA_reads": str(summary["na_reads"]),
            "HA_coverage": str(summary["hacoverage"]),
            "NA_coverage": str(summary["nacoverage"]),
            "flu_clade": summary["clade_call"],
            "rag_status": summary["res_conf"],
        },
    }

    results_fail = analysis.add_results(
        top_result=summary["subtype_call"],
        results_dict=result_fields,
    )

    analysis.add_server_records(
        sample_id=summary["climb_id"],
        server_name=server,
    )

    required_failed, attribute_failed = analysis.check_analysis_object(
        publish_analysis=False
    )

    failed = any([
        methods_fail,
        versions_fail,
        results_fail,
        required_failed,
        attribute_failed,
    ])

    return analysis, int(failed)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Summarise flu mapping output and create an Onyx analysis-fields JSON."
        )
    )
    parser.add_argument("--climb-id", required=True)
    parser.add_argument("--mapped-tab", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--server", required=True)
    parser.add_argument("--pipeline-info", required=True)
    parser.add_argument("--orange-box-version", default="unknown")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    segment_table, summary = analyze_mapping(args.mapped_tab, args.climb_id)

    segment_table_path = (
        args.output_dir / f"{args.climb_id}_segment_mapping_summary.csv"
    )
    summary_json_path = (
        args.output_dir / f"{args.climb_id}_flu_subtyping_summary.json"
    )
    onyx_json_path = (
        args.output_dir / f"{args.climb_id}.flu_subtyping.analysis_fields.json"
    )

    segment_table.to_csv(segment_table_path, index=False)
    summary_json_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    pipeline_info = make_pipeline_dict(args.pipeline_info)
    analysis, exit_code = create_analysis_fields(
        summary=summary,
        server=args.server,
        pipeline_info=pipeline_info,
        orange_box_version=args.orange_box_version,
    )

    if exit_code:
        raise RuntimeError("Onyx analysis fields failed validation")

    analysis.write_analysis_to_json(result_file=onyx_json_path)

    # Debug: show the actual fields that were written
    payload = json.loads(onyx_json_path.read_text())
    print("Top-level keys:", sorted(payload.keys()))
    print("result_metrics:", json.loads(payload["result_metrics"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())