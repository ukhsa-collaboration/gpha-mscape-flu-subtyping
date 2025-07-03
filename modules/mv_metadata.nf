#!/usr/bin/env nextflow

nextflow.enable.dsl=2



process MV_METADATA{
    tag "${metadata}"
    container 'community.wave.seqera.io/library/pandas:2.3.0--4f0f0d6a0c80ada7'
    publishDir "${params.outdir}", mode: 'copy'
    
    input:
    path(metadata)

    output:
    path("metadata.csv"), emit: md_table
    
    script:
    """
    cp ${metadata} ./metadata.csv
   
    """
}