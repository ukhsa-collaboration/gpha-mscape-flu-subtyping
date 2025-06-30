#!/usr/bin/env nextflow
// nextflow.enable.dsl=2
include { FLUSUB_ANALYSIS } from './subworkflows/flusub_analysis'

def helpMessage() {
  log.info """
        Usage:
        The typical command for running the pipeline is as follows:
        nextflow run main.nf --samplesheet sample-sheet.csv --metadata metadata.csv --outdir "output_directory"

        Mandatory arguments:
         --samplesheet                        ClimbID to be subtyped
         --metadata                        Metadata for ClimbIDs
         --outdir                       Output directory to place final tables

       Optional arguments:

         --help                         This usage statement.
        """
}

// Show help message
if (params.help) {
    helpMessage()
    exit 0
}

if (!params.samplesheet) {
    error "Please provide a samplesheet with --samplesheet"
}

if (!params.metadata) {
    error "Please provide the metadata with --metadata"
}

// Define a channel from the sample sheet
samples = Channel
    .fromPath(params.samplesheet)
    .splitCsv(header: true)
    .map { row ->
        def climb_id = row.climb_id
        def fastq1 = row.human_filtered_reads_1
        def fastq2 = row.containsKey('human_filtered_reads_2') ? row.human_filtered_reads_2 : null
        return fastq2 ? tuple(climb_id, fastq1, fastq2) : tuple(climb_id, fastq1)
    }
    .branch{ v ->
        paired_end: v.size() == 3
        single_end: v.size() == 2 
    }
    // // Assign the separated channels
    .set { ch_fastqs }  // Define separate channels


workflow {
    // handle input parameters
    log.info "Samplesheet: ${params.samplesheet}"
    log.info "Metadata table: ${params.metadata}"
    log.info "Output directory: ${params.output}"
    log.info "Number of CPUs (Max): ${params.max_cpus}"
    
        
    // Run subworkflows
    FLUSUB_ANALYSIS(ch_fastqs.single_end)
}
