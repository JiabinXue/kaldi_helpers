#!/usr/bin/python3

"""
Given a json file with transcript information these tools can perform
# manipulations including generating word lists or filtering output to
# exclude english/punctuation.
# Optionally provide the output json file name with -j
# Usage: python clean_json.py --infile file_in.json [--outfile file_out.json] [-re|--removeEng] [-ul|--useLangid]

EXAMPLE_JSON_DATA = [
    {"transcript": "Comment t'appelles tu?"},
    {"transcript": "Je m'appelle François."},
    {"transcript": "Est-ce tu a une livre préférér."},
    {"transcript": "Oui, j'adore L'Histoire Secrète par Donna Tartt."},
    {"transcript": "Vraiment? Je n'ai jamais lu ça."},
]
"""

import re
import string
import sys
import nltk
from argparse import ArgumentParser
from langid.langid import LanguageIdentifier, model
from nltk.corpus import words
from typing import Dict, List, Set
from src.utilities import load_json_file, write_data_to_json_file


def get_english_words() -> Set[str]:
    """
    Gets a list of English words from the nltk corpora (~235k words).
    N.B: will download the word list if not already available (~740kB), requires internet.
    :return: a set containing the English words
    """
    nltk.download("words")  # Will only download if not locally available.
    return set(words.words())


def clean_utterance(utterance: Dict[str, str],
                    remove_english: bool = False,
                    english_words: set = None,
                    punctuation: str = None,
                    special_cases: List[str] = None) -> (List[str], int):
    """
    Takes an utterance and cleans it based on the rules established by the provided parameters.
    :param utterance: a dictionary with a "transcript" key-value pair.
    :param remove_english: whether or not to remove English words.
    :param english_words: a list of english words to remove from the transcript (we suggest the nltk words corpora).
    :param punctuation: list of punctuation symbols to remove from the transcript.
    :param special_cases: a list of words to always remove from the output.
    :return: a tuple with a list of 'cleaned' words and a number representing the number of English words to remove.
    """
    translation_tags = {"@eng@", "<ind:", "<eng:"}
    utterance_string = utterance.get("transcript").lower()
    words = utterance_string.split()
    clean_words = []
    english_word_count = 0
    for word in words:
        if special_cases and word in special_cases:
            continue
        if word in translation_tags:  # Translations / ignore
            return [], 0
        # If a word contains a digit, throw out whole utterance
        if bool(re.search(r"\d", word)) and not word.isdigit():
            return [], 0
        if punctuation:
            for mark in punctuation:
                word = word.replace(mark, "")
        if remove_english and len(word) > 3 and word in english_words:
            english_word_count += 1
            continue
        clean_words.append(word)
    return clean_words, english_word_count


def is_valid_utterance(clean_words: List[str],
                       english_word_count: int,
                       remove_english: bool,
                       use_langid: bool,
                       langid_identifier: LanguageIdentifier) -> bool:
    """
    Determines whether a cleaned utterance (list of words) is valid based on the provided parameters.
    :param clean_words: a list of clean word strings.
    :param english_word_count: the number of english words removed from the string during cleaning.
    :param remove_english: whether or not to remove english words.
    :param use_langid: whether or not to use the langid library to determine if a word is English.
    :param langid_identifier: language identifier object to use with langid library.
    :return: True if utterance is valid, false otherwise.
    """
    # Exclude utterance if empty after cleaning
    cleaned_transcription = " ".join(clean_words).strip()
    if cleaned_transcription == "":
        return False

    # Exclude utterance if > 10% english
    if remove_english and len(clean_words) > 0 and english_word_count / len(clean_words) > 0.1:
        # print(round(english_word_count / len(clean_words)), trans, file=sys.stderr)
        return False

    # Exclude utterance if langid thinks its english
    if remove_english and use_langid:
        lang, prob = langid_identifier.classify(cleaned_transcription)
        if lang == "en" and prob > 0.5:
            return False
    return True


def clean_json_data(json_data: List[Dict[str, str]],
                    remove_english: bool = False,
                    use_langid: bool = False) -> List[Dict[str, str]]:
    """
    Clean a list of utterances (Python dictionaries) based on the given parameters.
    :param json_data: list of Python dictionaries, each must have a 'transcription' key-value.
    :param remove_english: whether or not to remove English from the utterances.
    :param use_langid: whether or not to use the langid library to identify English to remove.
    :return: cleaned list of utterances (list of dictionaries).
    """
    punctuation_to_remove = string.punctuation + "…’“–”‘°"
    special_cases = ["<silence>"]  # Any words you want to ignore
    langid_identifier = None

    if remove_english:
        english_words = get_english_words()  # pre-load English corpus
        if use_langid:
            langid_identifier = LanguageIdentifier.from_modelstring(model,
                                                                    norm_probs=True)
    else:
        english_words = set()

    cleaned_data = []
    for utterance in json_data:
        clean_words, english_word_count = clean_utterance(utterance=utterance,
                                                          remove_english=remove_english,
                                                          english_words=english_words,
                                                          punctuation=punctuation_to_remove,
                                                          special_cases=special_cases)

        if is_valid_utterance(clean_words,
                              english_word_count,
                              remove_english,
                              use_langid,
                              langid_identifier):
            cleaned_transcript = " ".join(clean_words).strip()
            utterance["transcript"] = cleaned_transcript
            cleaned_data.append(utterance)

    return cleaned_data


def main() -> None:
    """
    Run the entire clean_json process as a command line utility.
    Usage: python clean_json.py --infile file_in.json [--outfile file_out.json] [-re|--removeEng] [-ul|--useLangid]
    """
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument("--infile", type=str, help="The input file to clean.")
    parser.add_argument("--outfile", type=str, help="The file to write to")  # Default to stdout if not provided
    parser.add_argument("-r", "--removeEng", help="Remove english like utterances", action="store_true")
    parser.add_argument("-u", "--useLangId", help="Use langid library to detect English", action="store_true")
    arguments = parser.parse_args()

    data = load_json_file(arguments.infile)
    outfile = arguments.outfile if arguments.outfile else sys.stdout

    print(f"Filtering {str(arguments.infile)}...", end="", flush=True, file=outfile)

    filtered_data = clean_json_data(list(data),
                                    remove_english=arguments.removeEng,
                                    use_langid=arguments.useLangId)

    write_data_to_json_file(data=list(filtered_data),
                            output=outfile)

    print(f"Finished! Wrote {str(len(filtered_data))} transcriptions.", end="", flush=True, file=outfile)


if __name__ == "__main__":
    main()
