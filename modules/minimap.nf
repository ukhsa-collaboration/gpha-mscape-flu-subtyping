#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process RUN_MINIMAP_SE{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/minimap2:2.30--dde6b0c5fbc82ebd'
    publishDir "${params.outdir}/${climb_id}", mode: 'copy'
    
    input:
    tuple val(climb_id), path(fastq1), path(minimap_reference)

    output:
    tuple  val(climb_id), path("flusub_complete.txt"), path('*.flusub.mapped.tab'), emit: mappedreads
    
    
    script:
    """
    set +e
    minimap2 ${params.minimap2_single_options} --secondary=no ${minimap_reference} ${fastq1} > ${climb_id}.flusub.mapped.tab
    rm *gz
    exit_status=\$?
    if [ \$exit_status -eq 0 ] ; then
        echo "True" > flusub_complete.txt
        exit 0
    elif grep -q "ERROR:" flusub.mapped.tab ; then
        echo "False" > flusub_complete.txt
        exit 0
    else
        exit \$exit_status
    fi
    """
}

process RUN_MINIMAP_PE{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/minimap2:2.30--dde6b0c5fbc82ebd'
    publishDir "${params.outdir}/${climb_id}", mode: 'copy'
    
    input:
    tuple val(climb_id), path(fastq1), path(fastq2), path(minimap_reference)

    output:
    tuple  val(climb_id), path("flusub_complete.txt"), path('*.flusub.mapped.tab'), emit: mappedreads
    
    
    script:
    """
    set +e
    minimap2 ${params.minimap2_paired_options} --secondary=no ${minimap_reference} ${fastq1} ${fastq2} > ${climb_id}.flusub.mapped.tab
    rm *gz
    exit_status=\$?
    if [ \$exit_status -eq 0 ] ; then
        echo "True" > flusub_complete.txt
        exit 0
    elif grep -q "ERROR:" flusub.mapped.tab ; then
        echo "False" > flusub_complete.txt
        exit 0
    else
        exit \$exit_status
    fi
    """
}
