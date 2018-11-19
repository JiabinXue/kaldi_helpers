#!/usr/bin/python3.6

"""
# Copyright 2018 The University of Queensland (Author: Nicholas Lambourne)
# LICENCE: MIT
"""

from argparse import ArgumentParser
from pathlib import Path
from pympi import Praat, Elan


def get_first_wav(wav_scp: str) -> str:
    with open(wav_scp, "r") as scp:
        return scp.readline().split(" ")[1]


def main() -> None:
    parser: ArgumentParser = ArgumentParser(description="Converts Praat TextGrid format to ELAN eaf Format.")
    parser.add_argument("--tg", "--textgrid", type=str, help="The input_scripts TextGrid format file", required=True)
    parser.add_argument("--wav", type=str, help="The relative path to the .wav file associated with the TextGrid",
                        required=True)
    parser.add_argument("-o", "--outfile", type=str, help="The file path for the ELAN file output_scripts",
                        default="./inferred-aligned.eaf")
    arguments = parser.parse_args()

    textgrid_file = arguments.tg
    wav_file = Path(get_first_wav(arguments.wav))
    output_file = Path(arguments.outfile)

    if not output_file.parent:
        Path.mkdir(output_file.parent, parents=True)

    textgrid = Praat.TextGrid(file_path=textgrid_file)

    elan = textgrid.to_eaf()

    elan.add_linked_file(file_path=str(wav_file.absolute()),
                         relpath=str(wav_file),
                         mimetype=Elan.Eaf.MIMES.get("wav", ""),
                         time_origin=0)

    elan.to_file(output_file)


if __name__ == '__main__':
    main()
