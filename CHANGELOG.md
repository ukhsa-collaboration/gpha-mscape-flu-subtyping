<<<<<<< HEAD
# Changelog

Notable changes to the mSCAPE flu-subtyping pipeline are recorded here.

## Unreleased — `dev/cherami`

- Implemented a Nextflow DSL2 workflow for single-end and paired-end flu-subtyping samples using Minimap2.
- Added mapping summarization outputs: a flu-subtyping summary JSON, per-segment mapping-summary CSV, and Onyx analysis-fields JSON.
- Added the `pipeline_command` string to the analysis-fields JSON. It describes the Minimap2, summarization, and Quarto stages with placeholders rather than recording fully resolved runtime arguments.
- Added per-sample Quarto HTML report generation.
- Added workflow steps for writing/updating/publishing Onyx analysis records and uploading mapped results, segment summaries, and HTML reports to S3.
- Added a sample-sheet generator that retrieves read locations and metadata from Onyx for a list of CLIMB IDs.
- Documented inputs, execution, outputs, and environment-specific dependencies in the README.

### Current implementation notes

- Minimap2 is used for both single-end and paired-end samples. BWA-MEM is not currently part of the workflow.
- The summarizer expects Minimap2 mapping-table input; using BWA-MEM will require a conversion step or SAM-format support in the summarizer.
=======
mSCAPE Template - Version 0.2.0
Now has added features:
- updated the pre-commit config to implement search for climb IDs on commit.
- added branch protection json
- dynamic versioning through version set in __init__.py in package directory and set in pyproject.toml
- removed fixed versions of ruff so the version should match the GitHub actions.
>>>>>>> e5678ceaaf8341addfb3d98fdc0dab0f49fc5217
