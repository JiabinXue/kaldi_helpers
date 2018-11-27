#!/usr/bin/python3

"""
Automatically build a word->sound dictionary
Input: text file, config file, output file name
Output: mapping between unique words and their sound, ordered by their appearance
Usage:
       python3.6 {{ .INPUT_SCRIPTS_PATH }}/make_prn_dict.py
                --infile wordlist.txt
                --outfile lexicon.txt
                --config letter_to_sound
"""

import argparse
import sys
from typing import List, Tuple


def parse_input(input_file_name: str) -> List[str]:
    """
    Reads in the list of words to create a pronunciation dictionary for.
    :param input_file_name: file path of the word list input file
    :return: a simple list of words
    """
    with open(input_file_name, "r", encoding='utf-8') as input_file:
        input_tokens = []
        for line in input_file.readlines():
            token = line.strip()
            if len(token) > 0:
                input_tokens.append(token)
        return input_tokens


def parse_configs(config_file_name: str) -> List[Tuple[str, str]]:
    """
    Reads in the mappings of letters to sounds
    :param config_file_name: the name of the file containing character pronunciation
    mappings
    :return: a list of tuples mapping characters to their respective sounds.
    """
    with open(config_file_name, "r", encoding='utf-8') as config_file:
        sound_mappings = []
        for line in config_file.readlines():
            if line[0] == '#':
                continue
            mapping = list(filter(None, line.strip().split(' ', 1)))
            if len(mapping) > 1:
                sound_mappings.append((mapping[0], mapping[1]))
            # Sort the sound mappings by length of sound mapping
        sound_mappings.sort(key=lambda x: len(x[0]), reverse=True)
        return sound_mappings


def generate_dictionary(input_file_name: str,
                        output_file_name: str,
                        config_file_name: str) -> None:
    """
    Create a pronunciation dictionary mapping
    :param input_file_name: file path of the wordlist input file
    :param output_file_name: file path of the lexicon output file
    :param config_file_name: file path with one letter -> sound mapping in each line
    """
    # Read the input_scripts file
    input_tokens = parse_input(input_file_name)

    # Read the config file
    sound_mappings = parse_configs(config_file_name)

    oov_characters: set = {}  # Characters not found in mapping

    output_file = open(output_file_name, "w", encoding='utf-8')
    output_file.write('!SIL sil\n')
    output_file.write('<UNK> spn\n')
    for token in input_tokens:
        current_index = 0
        res = [token]
        token_lower = token.lower()

        while current_index < len(token_lower):
            found = False
            for maps in sound_mappings:
                if token_lower.find(maps[0], current_index) == current_index:
                    found = True
                    res.append(maps[1])
                    current_index += len(maps[0])
                    break

            if not found:  # Unknown sound
                res.append('(' + token_lower[current_index] + ')')
                oov_characters.add(token_lower[current_index])
                current_index += 1

        output_file.write(' '.join(res) + '\n')

    output_file.close()

    for character in oov_characters:
        print(f"Unexpected character: {character}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", help="The file path of the wordlist input file (one word per line)", required=True)
    parser.add_argument("--outfile", help="The file path of the lexicon output file", required=True)
    parser.add_argument("--config", help="Configuration file path with one letter -> sound mapping in each line")
    arguments = parser.parse_args()

    generate_dictionary(input_file_name=arguments.infile,
                        output_file_name=arguments.outfile,
                        config_file_name=arguments.config)

    print("PRN dictionary (lexicon) created!", file=sys.stderr)


if __name__ == "__main__":
    main()
