
# mSCAPE Flu Subtyping Nextflow Pipeline

A Nextflow DSL2 pipeline for flu subtyping of human-filtered sequencing reads. It maps single-end and paired-end reads against an influenza reference with Minimap2, summarizes the mapping results, renders a per-sample Quarto report, and prepares analysis data for Onyx and S3.

## Workflow overview

For each sample, the workflow:

1. Maps reads using Minimap2. Single-end and paired-end samples use their configured Minimap2 options.
2. Creates a flu-subtyping summary JSON, a per-segment mapping-summary CSV, and an Onyx analysis-fields JSON.
3. Renders a per-sample HTML report with Quarto.
4. Uses the Onyx helper processes to write/update analysis records, upload the mapped table, segment summary and HTML report to S3, and publish the analysis.

The generated analysis-fields JSON includes pipeline metadata and a `pipeline_command` string describing the main steps. This field has a limit of 200 characters so is not a literal record of every command.

The current workflow uses Minimap2 for both read layouts. BWA-MEM is not currently used; adopting it would require converting its SAM output to the format expected by the flu-mapping summarizer or adding SAM support there.

## Requirements and environment

- Nextflow, using a version supported by the project configuration.
- Docker or another configured Nextflow execution profile.
- Access to input FASTQ files, the influenza reference FASTA, and the Quarto report assets.
- Onyx credentials and permission to query/write records in the selected project. Set `ONYX_TOKEN` and `ONYX_DOMAIN` in the environment.
- S3 credentials and endpoint configuration appropriate to the target bucket/environment.

The current configuration references shared UKHSA paths for the Minimap2 reference and Quarto assets. Make these paths available to the execution environment, or update the configuration/process paths for another environment. Use the appropriate authorized server and bucket; do not test against production resources unless authorized.

## Installation


Clone repo and create environment:

`git clone git@github.com:ukhsa-collaboration/gpha-mscape-flu-subtyping.git`

`conda env create -n flusub `

`conda activate flusub`


## Run the pipeline

```bash
nextflow run main.nf \
  --profile docker \
  --samplesheet input_files/<timestamp>-sample-sheet-nf.csv \
  --metadata input_files/<timestamp>-samplesheet-flu-metadata.csv \
  --outdir out_dir \
  --server devscape \
  --bucket ukhsa-devscape-scratch
```

Adjust the server and bucket for the intended environment. Parameters including `samplesheet`, `metadata`, `outdir`, `server`, `bucket`, `context`, `pipeline_info`, and `minimap_reference` are configured by `main.nf` and `nextflow.config`. See those files for the current defaults and profiles.

## Outputs

Outputs are organized by CLIMB ID under the output directory. They include:

- Minimap2 mapping table (`*.flusub.mapped.tab`) and mapping-completion status.
- Flu-subtyping summary JSON (`*_flu_subtyping_summary.json`). # Used by the quarto report only
- Segment-mapping summary CSV (`*_segment_mapping_summary.csv`).
- Onyx analysis-fields JSON (`*.flu_subtyping.analysis_fields.json`), including the `pipeline_command` field.
- Quarto HTML report (`*_summarise_mapping.html`).
- Onyx/S3 helper output files and logs.
- Nextflow execution timeline, report, trace, and DAG files where enabled by configuration.

Only samples whose mapping completion status is successful are intended for the S3-upload step.

## Configuration notes

- Minimap2 reference and options are set in `nextflow.config`.
- `RUN_QUARTO` expects the report QMD, Quarto configuration, and extensions at the shared paths specified in `modules/summarise_results.nf`.
- The mapping summarizer consumes the Minimap2 mapping-table format; a mapper change may require an output-conversion step or summarizer changes.
- Onyx write, update, and publish operations require valid credentials and appropriate permissions.

