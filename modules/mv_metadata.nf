#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process MV_METADATA{
    tag "${params.metadata}"
    publishDir "${params.outdir}", mode: 'copy'
    
    input:
    path(${params.metadata})

    output:
    path("metadata.csv"), emit: md_table
    
    
    script:
    """
    
    cp ${params.metadata} ${params.output}/metadata.csv
    
   
    """
}