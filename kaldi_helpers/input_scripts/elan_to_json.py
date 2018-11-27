#!/usr/bin/python3

"""
Get all files in the repository can use recursive atm as long as we don't need numpy
pass in corpus path throw an error if matching file wav isn"t found in the corpus directory

Usage: python3 elan_to_json.py [-h] [-i INPUT_DIR] [-o OUTPUT_DIR] [-t TIER] [-j OUTPUT_JSON]
"""

import glob
import sys
import os
import argparse
from pympi.Elan import Eaf
from typing import List
from kaldi_helpers.script_utilities import find_files_by_extension
from kaldi_helpers.script_utilities import write_data_to_json_file


def process_eaf(input_elan_file: str, tier_name: str) -> List[dict]:
    """
    Method to process a particular tier in an eaf file (ELAN Annotation Format). It stores the transcriptions in the 
    following format:
                    {'speaker_id': <speaker_id>,
                    'audio_file_name': <file_name>,
                    'transcript': <transcription_label>,
                    'start_ms': <start_time_in_milliseconds>,
                    'stop_ms': <stop_time_in_milliseconds>}
                    
    :param input_elan_file: name of input_scripts elan file
    :param tier_name: name of the elan tier to process. these tiers are nodes from the tree structure in the .eaf file.
    :return: 
    """
    # Get paths to files
    input_directory, full_file_name = os.path.split(input_elan_file)
    file_name, extension = os.path.splitext(full_file_name)

    input_eaf = Eaf(input_elan_file)

    # Default to first tier if given tier not found.
    tier_names = input_eaf.get_tier_names()
    if tier_name not in tier_names:
        print("WARNING: Provided tier not found, defaulting to first tier")
        tier_name = tier_names[0]

    # Look for wav file matching the eaf file in same directory
    if os.path.isfile(os.path.join(input_directory, file_name + ".wav")):
        print("WAV file found for " + file_name, file=sys.stderr)
    else:
        raise ValueError(f"WAV file not found for {full_file_name}. "
                         f"Please put it next to the eaf file in {input_directory}.")

    # Get first tier by default if not provided or not valid
    if not tier_name or tier_name not in input_eaf.get_tier_names():
        print("No tier provided or tier name invalid")
        tier_name = input_eaf.get_tier_names()[0]

    # Get annotations and parameters (things like speaker id) on the target tier
    annotations = sorted(input_eaf.get_annotation_data_for_tier(tier_name))

    parameters = input_eaf.get_parameters_for_tier(tier_name)
    speaker_id = parameters.get("PARTICIPANT", "")

    annotations_data = []

    for annotation in annotations:
        start = annotation[0]
        end = annotation[1]
        annotation = annotation[2]

        # print("processing annotation: " + annotation, start, end)
        obj = {
            "audio_file_name": f"{file_name}.wav",
            "transcript": annotation,
            "start_ms": start,
            "stop_ms": end
        }
        if "PARTICIPANT" in parameters:
            obj["speaker_id"] = speaker_id
        annotations_data.append(obj)

    return annotations_data


def main():

    """ 
    Run the entire elan_to_json.py as a command line utility. It extracts information on speaker, audio file, 
    transcription etc. from the given tier of the specified .eaf file. 
    
    Usage: python3 elan_to_json.py [-h] [-i INPUT_DIR] [-o OUTPUT_DIR] [-t TIER] [-j OUTPUT_JSON]
    """

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
                            description="This script takes an directory with ELAN files and "
                                        "slices the audio and output_scripts text in a format ready "
                                        "for our Kaldi pipeline.")
    parser.add_argument("-i", "--input_dir",
                        help="Directory of dirty audio and eaf files",
                        default="working_dir/input/data/")
    parser.add_argument("-o", "--output_dir",
                        help="Output directory",
                        default="../input/output/tmp/")
    parser.add_argument("-t", "--tier",
                        help="Target language tier name")
    parser.add_argument("-j", "--output_json",
                        help="File name to output_scripts json")
    arguments: argparse.Namespace = parser.parse_args()

    # Build output_scripts directory if needed
    if not os.path.exists(arguments.output_dir):
        os.makedirs(arguments.output_dir)

    all_files_in_directory = set(glob.glob(os.path.join(arguments.input_dir, "**"), recursive=True))
    input_eaf_files = find_files_by_extension(all_files_in_directory, {"*.eaf"})

    annotations_data = []

    for input_eaf_file in input_eaf_files:
        annotations_data.extend(process_eaf(input_eaf_file, arguments.tier))

    write_data_to_json_file(annotations_data, arguments.output_json)


if __name__ == "__main__":
    main()

