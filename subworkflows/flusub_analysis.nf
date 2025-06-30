#!/usr/bin/env nextflow
nextflow.enable.dsl=2


include {RUN_MINIMAP} from "../modules/minimap"
include {RUN_QUARTO} from "../modules/summarise_results"
include {MV_METADATA} from "../modules/mv_metadata"

workflow FLUSUB_ANALYSIS {
    take:
    single_end_ch

    main:
    // 1 - Run mapping
    RUN_MINIMAP(single_end_ch)

    // 2 - Move metadata table
    MV_METADATA(${params.metadata})
    
    // 3 - Create summary outputs
    RUN_QUARTO(RUN_MINIMAP.out)
}