#!/usr/bin/env python3

import csv
import logging
import multiprocessing
import os
from typing import TypedDict

from text_quality.classifier.pipeline import ClassifierScores, Pipeline
from text_quality.feature.featurize import Featurizer, Scorers
from text_quality.feature.scorer.dictionary import HunspellDictionary, TokenDictionary
from text_quality.feature.scorer.garbage import GarbageDetector
from text_quality.feature.scorer.q_gram import QGram
from text_quality.feature.tokenizer import NautilusOcrTokenizer
from text_quality.page.page import Page
from text_quality.settings import (
    HUNSPELL_DIR,
    HUNSPELL_LANGUAGE,
    LOG_LEVEL,
    PIPELINE_FILE,
    QGRAMS_FILE,
    TOKEN_DICT_FILE,
)
from tqdm import tqdm

logging.basicConfig(level=LOG_LEVEL)

tokenizer = NautilusOcrTokenizer()

featurizer = Featurizer(
    Scorers(
        dict_score=HunspellDictionary.from_path(HUNSPELL_DIR, HUNSPELL_LANGUAGE),
        dict_score_gt=TokenDictionary.from_file(TOKEN_DICT_FILE),
        n_gram_score=QGram.from_file(QGRAMS_FILE),
        garbage_score=GarbageDetector(),
    ),
    tokenizer=tokenizer,
)
pipeline = Pipeline.from_file(PIPELINE_FILE, featurizer)
if pipeline.features != featurizer.features:
    raise RuntimeError(
        f"Pipline input features ({pipeline.features}) do not match scorers ({featurizer.features})."
    )


class OutputRow(TypedDict):
    filename: str
    quality_class: int


def analyse_folder(filepaths, outfilepath):
    pagexml_inputs = {}
    for pagexml in filepaths:
        if pagexml in pagexml_inputs:
            logging.warning("Duplicate input file: '%s'", pagexml)
        try:
            pagexml_inputs[pagexml] = Page.from_file(pagexml).get_text()
        except Exception as e:
            logging.error("Error parsing file '%s': %s", pagexml, str(e))
            pagexml_inputs[pagexml] = ""

    fieldnames = list(OutputRow.__annotations__.keys())
    fieldnames += list(ClassifierScores.__annotations__.keys()) + ["Reason"]

    with open(outfilepath, "w") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for name, text in tqdm(pagexml_inputs.items(), desc="Processing", unit="file"):
            quality_class, classifier_scores, reason = pipeline.classify_with_scores(
                text
            )
            row = (
                OutputRow(filename=name, quality_class=quality_class)
                | classifier_scores
            )

            row = (
                OutputRow(filename=name, quality_class=quality_class)
                | classifier_scores
                | {"Reason": reason.name}
            )

            writer.writerow(row)


if __name__ == "__main__":
    # 2023_05
    BASE_FOLDER = "/media/leon/HDE00551/GLOBALISE/HTR/2023_05/"
    PAGEXML_FOLDER = os.path.join(BASE_FOLDER, "1.04.02")

    job_args = []
    for inventory_number in os.listdir(PAGEXML_FOLDER):
        pagexml_inputs = []
        files = os.listdir(os.path.join(PAGEXML_FOLDER, inventory_number, "page"))

        for f in files:
            filepath = os.path.join(PAGEXML_FOLDER, inventory_number, "page", f)
            if filepath.endswith(".xml"):
                pagexml_inputs.append(filepath)

        os.makedirs(os.path.join(BASE_FOLDER, "lahter"), exist_ok=True)
        outfilepath = os.path.join(
            BASE_FOLDER, "lahter", "classifications_" + inventory_number + ".csv"
        )

        job_args.append((pagexml_inputs, outfilepath))

    with multiprocessing.Pool(processes=max(8, 1)) as pool:
        pool.starmap(analyse_folder, job_args)

    # 2023_09
    BASE_FOLDER = "/media/leon/HDE00551/GLOBALISE/HTR/2023_09/"
    PAGEXML_FOLDER = os.path.join(BASE_FOLDER, "pagexml")

    job_args = []
    for inventory_number in os.listdir(PAGEXML_FOLDER):
        pagexml_inputs = []
        files = os.listdir(os.path.join(PAGEXML_FOLDER, inventory_number))

        for f in files:
            filepath = os.path.join(PAGEXML_FOLDER, inventory_number, f)
            if filepath.endswith(".xml"):
                pagexml_inputs.append(filepath)

        os.makedirs(os.path.join(BASE_FOLDER, "lahter"), exist_ok=True)
        outfilepath = os.path.join(
            BASE_FOLDER, "lahter", "classifications_" + inventory_number + ".csv"
        )

        job_args.append((pagexml_inputs, outfilepath))

    with multiprocessing.Pool(processes=max(8, 1)) as pool:
        pool.starmap(analyse_folder, job_args)
