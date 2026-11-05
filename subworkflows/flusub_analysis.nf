#!/usr/bin/env nextflow

nextflow.enable.dsl=2

include { RUN_MINIMAP_SE } from "../modules/minimap"
include { RUN_MINIMAP_PE } from "../modules/minimap"
include { RUN_QUARTO } from "../modules/summarise_results"
include { SUMMARISE_FLU_MAPPING } from "../modules/summarise_results"
include { MV_METADATA } from "../modules/mv_metadata"
include { ONYX_WRITE } from "../modules/onyx_write"
include { S3_UPLOAD } from "../modules/s3_upload"
include { ONYX_UPDATE } from "../modules/onyx_update"
include { ONYX_PUBLISH } from "../modules/onyx_publish"

workflow FLUSUB_ANALYSIS {
    take:
    metadata
    single_end_reads
    paired_end_reads
    server
    bucket
    context
    pipeline_info
    onyx_status

    main:
    MV_METADATA(metadata)

    ch_minimap_single = single_end_reads.map { climb_id, read1 ->
        tuple(climb_id, read1, file(params.minimap_reference))
    }

    ch_minimap_paired = paired_end_reads.map { climb_id, read1, read2 ->
        tuple(climb_id, read1, read2, file(params.minimap_reference))
    }

    RUN_MINIMAP_SE(ch_minimap_single)
    RUN_MINIMAP_PE(ch_minimap_paired)

    ch_mapped_reads = RUN_MINIMAP_SE.out.mappedreads
        .mix(RUN_MINIMAP_PE.out.mappedreads)
    
    // Retain the sample ID and completion status; normalize the mapped-file value.
    flu_sub = ch_mapped_reads.map { climb_id, minimap_complete, mapped_tab ->
        def mapped_file = mapped_tab instanceof List ? mapped_tab[0] : mapped_tab
        tuple(climb_id, minimap_complete, mapped_file)
    }


     summary_input = flu_sub.map { climb_id, minimap_complete, mapped_file ->
        tuple(
            climb_id,
            mapped_file,
            server,
            context,
            pipeline_info
        )
    }


    SUMMARISE_FLU_MAPPING(summary_input)

    // Pass all inputs to RUN_QUARTO as one tuple per sample.
    quarto_input_ch = SUMMARISE_FLU_MAPPING.out.summary.map {
    climb_id, summary_json, segment_summary_csv ->
    tuple(climb_id, summary_json, segment_summary_csv, metadata)
    }

    RUN_QUARTO(quarto_input_ch)

    onyx_input_ch = SUMMARISE_FLU_MAPPING.out.summary
        .map { climb_id, summary_json, segment_summary_csv ->
            tuple(climb_id, summary_json)
        }

    //ONYX_WRITE(onyx_input_ch,server)

    // Join by climb_id so the mapping file and Quarto report stay together.
    //ch_s3_inputs = flu_sub
    //    .join(RUN_QUARTO.out.html)
    //    .join(ONYX_WRITE.out.analysis_id)
    //    .filter {
     //       climb_id, minimap_complete, mapped_file, html, analysis_id ->
      //      minimap_complete.text.contains("True")
       // }
     //   .map {
       //     climb_id, minimap_complete, mapped_file, html, analysis_id ->
      //      tuple(climb_id, [mapped_file, html], analysis_id)
       // }

    //S3_UPLOAD(ch_s3_inputs, server, bucket)

    //ch_update_inputs = ONYX_WRITE.out.analysis_id
    //    .join(S3_UPLOAD.out.s3_locations)

    //ONYX_UPDATE(ch_update_inputs, server)

    //ch_publish = channel.of()
    //    .concat(
    //        ONYX_WRITE.out.analysis_id,
    //        ONYX_UPDATE.out.analysis_id.ifEmpty([[], []])
     //   )
     //   .collect()
     //   .map { meta_write, id_write, meta_update, id_update ->
      //      tuple(meta_write, id_write)
     //   }

    //ONYX_PUBLISH(server, ch_publish)

    emit:
    flusub_json = quarto_input_ch.map {
        climb_id, summary_json, segment_summary_csv, metadata ->
        summary_json
    }
    flusub_summary = RUN_QUARTO.out.html
    flusub_tab = quarto_input_ch.map {
        climb_id, summary_json, segment_summary_csv, metadata ->
        segment_summary_csv
    }
   // flusub_analysis_id = ONYX_PUBLISH.out.analysis_id
}