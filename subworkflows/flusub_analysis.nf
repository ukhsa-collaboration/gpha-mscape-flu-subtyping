#!/usr/bin/env nextflow
nextflow.enable.dsl=2


include {RUN_MINIMAP} from "../modules/minimap"
include {RUN_QUARTO} from "../modules/summarise_results"


workflow FLUSUB_ANALYSIS {
    take:
    single_end_ch

    main:
    // 1 - Run mapping
    RUN_MINIMAP(single_end_ch)

    // 2 - Create summary outputs
    RUN_QUARTO(RUN_MINIMAP.out)
}