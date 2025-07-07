#!/usr/bin/env python

import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient
import argparse
from pathlib import Path
import pandas as pd
import csv
import datetime

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)


def get_args() -> argparse.Namespace:
    """
    Command Line
    :return: argParse variable
    """
    parser = argparse.ArgumentParser(description="generate-sample-sheet")
    parser.add_argument("-i", "--input",
                help="input file containing CLIMB-IDs",
                required=True, type=Path)
    parser.add_argument("-o", "--output",
                help="Output directory for downloaded data",
                required=True, type=Path)

    parser.add_argument("-p","--project",help="project domain",required=True)

    args = parser.parse_args()
    return args

def parse_file(fp: Path):
    """
    Read in text file, seperate climb ids into lis
    :args: filepath str()
    """
    with open(fp, "r", encoding="utf-8-sig") as file:
        data = file.readlines()  # Reads lines into a list
        data = [line.strip() for line in data]  # Remove newline characters
        data = [s.replace('"', '') for s in data] # remove " from strings
        return data

def get_record_by_climb_id(climb_id_list: list):
    dict_list = []
    for id in climb_id_list:
        try:
            with OnyxClient(config) as client:
                    data = pd.DataFrame(client.filter(
                    project = project,
                    climb_id = id
                ))
        
            read_1_link = data["human_filtered_reads_1"][0]
            read_2_link = data["human_filtered_reads_2"][0]
            taxon_reports_dir = data["taxon_reports"][0]
            dict_list.append({'climb_id': id, 
                'human_filtered_reads_1': read_1_link, 
                'human_filtered_reads_2': read_2_link,
                'taxon_reports_dir': taxon_reports_dir,
                'kraken_assignments': os.path.join(
                    taxon_reports_dir,
                    str(id)+str('_PlusPF.kraken_assignments.tsv')),
                'kraken_report': os.path.join(
                taxon_reports_dir, 
                str(id)+str('_PlusPF.kraken_report.json'))
            })
        except KeyError:
            print(f"Sample {id} not found in database. Skipping.")
            pass
    return dict_list


def get_species_proportion(record_id, species):

    try:
        with OnyxClient(config) as client:
            record = client.get(
                project =project,
                climb_id = record_id)

        class_calls = pd.DataFrame(record['classifier_calls'])
        try:    
            unclass = class_calls.loc[class_calls['human_readable'] == 'unclassified', 'count_descendants'].item()
        except:
            unclass = 0
        try:
            root = class_calls.loc[class_calls['human_readable'] == 'root', 'count_descendants'].item()
        except:
            root = 0
        total_reads = unclass + root
        df_dict = {}
        for s in species:
            try:
                sp_reads = class_calls.loc[class_calls['human_readable'] == s, 'count_descendants'].item()
                sp_percen = class_calls.loc[class_calls['human_readable'] == s, 'percentage'].item()
                species_dict = {'climb_id': record_id,'Total_reads': total_reads, f'Kraken_{s}_reads': sp_reads, 
                   f'Percentage_{s}_reads': sp_percen}
            except:
                species_dict = {'climb_id': record_id,'Total_reads': total_reads, f'Kraken_{s}_reads': 0, 
                   f'Percentage_{s}_reads': 0}
            df_dict.update(species_dict)
    except KeyError:
            print(f"Sample {record_id} not found in database. Skipping.")
            pass
    return df_dict

def get_metadata_by_climb_id(climb_id_list: list):
    dict_list = []
    for id in climb_id_list:
        try:
            with OnyxClient(config) as client:
                    data = pd.DataFrame(client.filter(
                    project = project,
                    climb_id = id
                ))
        
            site = data["site"][0]
            read_2_link = data["human_filtered_reads_2"][0]
            taxon_reports_dir = data["taxon_reports"][0]
            dict_list.append({'climb_id': id, 
                'site': data["site"][0], 
                'sequence_purpose': data["sequence_purpose"][0],
                'input_type': data["input_type"][0],
                'sample_source': data["sample_source"][0],
                'kraken_report': os.path.join(
                taxon_reports_dir, 
                str(id)+str('_PlusPF.kraken_report.json'))
            })
        except KeyError:
            print(f"Sample {id} not found in database. Skipping.")
            pass
    return dict_list


def write_to_csv(dict_list: list, output: Path):
     """
     Write list of dictionaries to csv
     :args: [{CLIMB-ID, READ1, READ2}], Path(output)
     :return: save as csv
     """
     with open(output, mode="w", newline="") as file:
        # Define the column names (fieldnames)
        fieldnames = dict_list[0].keys()  # Extract keys from the first dictionary
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dict_list)
        
def main():
    filename1 = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    args = get_args()
    climb_id_list = parse_file(args.input)
    climb_id_list = list(filter(None, climb_id_list))

    global project
    project = args.project
    dict_list = get_record_by_climb_id(climb_id_list)
    write_to_csv(dict_list, os.path.join(args.output,f"{filename1}-sample-sheet-nf.csv"))
    metadata = get_metadata_by_climb_id(climb_id_list)
    md = pd.DataFrame.from_dict(metadata)
    print(md.shape)
    df_info = []
    for record in climb_id_list:
        print(record)
        try:
            
            df_dict = get_species_proportion(record, ["Alphainfluenzavirus","Betainfluenzavirus"])
    
            df_info.append(df_dict)
        except KeyError:
            print(f"Sample {record} not found in database. Skipping.")
            pass
        flu_df = pd.DataFrame(df_info)

    summary_meta = pd.merge(md,flu_df,left_on="climb_id",right_on="climb_id",how="left")
    summary_meta.to_csv(os.path.join(args.output,f"{filename1}-samplesheet-flu-metadata.csv"),index=False)
    
    
if __name__ == "__main__":
    main()
