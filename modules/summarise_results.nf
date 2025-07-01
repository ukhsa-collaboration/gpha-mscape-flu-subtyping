#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process RUN_QUARTO{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/pandas_pip_jupyter-cache_onyx-client_pruned:9b8ef66786a23f5b'
    publishDir "${params.outdir}/${climb_id}", mode: 'copy'
    
    input:
    tuple val(climb_id), path(mappedreads)

    output:
    tuple  val(climb_id),
    path("${climb_id}_segment_mapping_summary.csv"),emit: mapping_summary
    path("${climb_id}_flusub_result.json"), emit: mapping_json
    path("${climb_id}_summarise_mapping.html"), emit: quarto_out
    
    
    script:
    """
    
    # Set environment variables needed for Quarto rendering
    export XDG_CACHE_HOME="./.xdg_cache_home"
    export XDG_DATA_HOME="./.xdg_data_home"
    
    cp $PWD/bin/summarise_mapping.qmd .
    cp $PWD/bin/_quarto.yml .
    cp -r $PWD/bin/_extensions .

    
    quarto render summarise_mapping.qmd --output '${climb_id}_summarise_mapping.html' -P climb_id:'${climb_id}' -P datapath:'flusub.mapped.tab' -P metadata:'$PWD/${params.outdir}/metadata.csv'
    
    """
}