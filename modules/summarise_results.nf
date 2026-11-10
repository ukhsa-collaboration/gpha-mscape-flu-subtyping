#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process RUN_QUARTO {
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/pandas_pip_jupyter-cache_onyx-client_pruned:9b8ef66786a23f5b'
    publishDir "${params.outdir}/${climb_id}", mode: 'copy'

    input:
    tuple val(climb_id),
          path(summary_json),
          path(segment_summary_csv),
          path(metadata_csv)

    output:

          tuple val(climb_id), path("${climb_id}_summarise_mapping.html"), emit: html

    script:
    """
    export XDG_CACHE_HOME="./.xdg_cache_home"
    export XDG_DATA_HOME="./.xdg_data_home"

    cp /shared/team/gpha-mscape-flu-subtyping/bin/flu_subtyping_report.qmd .
    cp /shared/team/gpha-mscape-flu-subtyping/bin/_quarto.yml .
    cp -r /shared/team/gpha-mscape-flu-subtyping/bin/_extensions .

    quarto render flu_subtyping_report.qmd \\
        --output '${climb_id}_summarise_mapping.html' \\
        -P climb_id:'${climb_id}' \\
        -P summary_json:'${summary_json}' \\
        -P segment_summary_csv:'${segment_summary_csv}' \\
        -P metadata_csv:'${metadata_csv}'
    """
}


process SUMMARISE_FLU_MAPPING {
    tag "${climb_id}"
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-onyx-analysis-helper:0.6.7'
    publishDir "${params.outdir}/${climb_id}", mode: 'copy'

    input:
    tuple val(climb_id),
          path(mapped_tab),
          val(server),
          val(context),
          val(pipeline_info)


    output:
    tuple val(climb_id),
          path("${climb_id}_flu_subtyping_summary.json"),
          path("${climb_id}_segment_mapping_summary.csv"),
          path("${climb_id}.flu_subtyping.analysis_fields.json"),
          emit: summary

    script:
    """
    summarise_flu_mapping.py \
          --climb-id $climb_id \
          --mapped-tab $mapped_tab \
          --output-dir . \
          --server $server \
          --pipeline-info $pipeline_info \
          --orange-box-version $context
    """
}