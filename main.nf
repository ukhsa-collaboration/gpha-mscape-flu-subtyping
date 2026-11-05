#!/usr/bin/env nextflow

include { FLUSUB_ANALYSIS } from './subworkflows/flusub_analysis'

def helpMessage() {
    log.info """
        Usage:
        nextflow run main.nf \\
            --samplesheet sample-sheet.csv \\
            --metadata metadata.csv \\
            --outdir output_directory \\
            --server server-name \\
            --bucket bucket-name \\
            --context context-value \\
            --pipeline_info pipeline-info

        Arguments:
         --samplesheet       Samples and FASTQ paths
         --metadata          Metadata for ClimbIDs
         --outdir            Output directory
         --server            Onyx server name
         --bucket            S3 bucket name
         --context           Context value for the analysis
         --pipeline_info     Pipeline information passed to Quarto

        Optional arguments:
         --help              Show this usage statement
    """
}

if (params.help) {
    helpMessage()
    exit 0
}

[
    samplesheet: params.samplesheet,
    metadata: params.metadata,
    outdir: params.outdir,
    
].each { name, value ->
    if (!value) {
        error "Please provide --${name.replace('_', '-')}."
    }
}

// Create channels from the sample sheet.
samples = Channel
    .fromPath(params.samplesheet)
    .splitCsv(header: true)
    .map { row ->
        def climb_id = row.climb_id
        def fastq1 = row.human_filtered_reads_1
        def fastq2 = row.containsKey('human_filtered_reads_2')
            ? row.human_filtered_reads_2
            : null

        fastq2
            ? tuple(climb_id, fastq1, fastq2)
            : tuple(climb_id, fastq1)
    }
    .branch { read_tuple ->
        paired_end: read_tuple.size() == 3
        single_end: read_tuple.size() == 2
    }
    .set { ch_fastqs }

    // Add the Minimap reference only to single-end tuples.
    
    ch_minimap_reads = ch_fastqs.single_end
        .map { climb_id, read1 ->
            tuple(climb_id, [read1], file(params.minimap_reference))
        }
        .mix(
            ch_fastqs.paired_end.map { climb_id, read1, read2 ->
                tuple(climb_id, [read1, read2], file(params.minimap_reference))
            }
        )
workflow {
    log.info "Samplesheet: ${params.samplesheet}"
    log.info "Metadata table: ${params.metadata}"
    log.info "Output directory: ${params.outdir}"
    log.info "Onyx server: ${params.server}"
    log.info "S3 bucket: ${params.bucket}"
    log.info "Pipeline info: ${workflow.manifest.name}, ${workflow.manifest.version}, ${workflow.manifest.homePage}"

    FLUSUB_ANALYSIS(
        params.metadata,
        ch_fastqs.single_end,
        ch_fastqs.paired_end,
        params.server,
        params.bucket,
        params.context,
        "'${workflow.manifest.name}, ${workflow.manifest.version}, ${workflow.manifest.homePage}'", 
        params.onyx_status
    )
}
