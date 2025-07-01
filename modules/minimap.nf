#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process RUN_MINIMAP{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/minimap2:2.30--dde6b0c5fbc82ebd'
    publishDir "${params.outdir}/${climb_id}", mode: 'copy'
    
    input:
    tuple val(climb_id), path(fastq1)

    output:
    tuple  val(climb_id), path('flusub.mapped.tab'), emit: mappedreads
    
    
    script:
    """
    minimap2 --secondary=no /shared/team/influenza-testing/nflow-test/bin/insaflu_refset_2025.fasta ${fastq1} > 'flusub.mapped.tab'
    rm *gz
    """
}