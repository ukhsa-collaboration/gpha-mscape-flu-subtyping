# mSCAPE Flu Subtyping NextFlow Pipeline

This pipeline will map the human_filtered.fastq.gz fraction to an INSAFLU reference set within the bin folder, then run a quarto report that contains the python code to summarise the mapping results by segment and subtype. 

First step, use bin/generate-sample-sheet.py to take an input list of Climb IDs to query onyx and provide input csv for the nextflow pipeline

```
python bin/generate-sample-sheet.py -h
usage: generate-sample-sheet.py [-h] -i INPUT -o OUTPUT

generate-sample-sheet

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        input file containing CLIMB-IDs
  -o OUTPUT, --output OUTPUT
                        Output directory for downloaded data
```

NextFlow Command  
```

nextflow run main.nf -profile docker --samplesheet sample-sheet.csv --outdir mapping-test
```

## To Do 
1. Tidy up config files to ensure parameters are tidy & consistent
2. Quarto report - add sample meta-data/ Qc section to report
