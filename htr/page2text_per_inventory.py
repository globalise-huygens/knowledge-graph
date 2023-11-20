import os
import xml.etree.ElementTree as ET

import multiprocessing

NS = {"prima": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"}

DISCLAIMER = """#+ DISCLAIMER:
#+ This transcription of documents of the Dutch East India Company (VOC) was 
#+ generated in September 2023 by the GLOBALISE project 
#+ (https://globalise.huygens.knaw.nl/) at the KNAW Humanities Cluster using
#+ the Loghi transcription software (https://github.com/knaw-huc/loghi).
#+ 
#+ Please note that the transcription will contain errors. It has not been 
#+ manually checked for accuracy or completeness. Some labels, 
#+ characterizations and information about persons, actions and events may
#+ be offensive and troubling to individuals and communities. Be careful 
#+ when relying on this transcription and be aware of its limitations.
#+ 
#+ This is the second version (v2.0) of this transcription. Please share your
#+ feedback through the contact form on 
#+ https://globalise.huygens.knaw.nl/contact-us/. In the future, improved 
#+ versions will be made available.
#+ 
#+ License: CC0 (http://creativecommons.org/publicdomain/zero/1.0). You are
#+ free to build upon, enhance, and reuse the transcription for any purposes
#+ without restriction.
#+ 
#+ Please reference the GLOBALISE project when using this transcription and 
#+ please retain this disclaimer when redistributing this file."""


def get_text_from_xml(file_data):
    tree = ET.parse(file_data)

    regions = tree.findall(".//prima:TextRegion", namespaces=NS)

    text_lines = []

    for region in regions:
        lines = region.findall(
            "prima:TextLine/prima:TextEquiv/prima:Unicode",
            namespaces=NS,
        )

        text_lines += (line.text for line in lines)

    return text_lines


def process_folder(folder_path):
    inventory_number = folder_path.split("/")[-1]

    # If file exists already, skip
    if os.path.exists(f"txt/{inventory_number}.txt"):
        print("Skipping:", inventory_number)
        return

    print("Processing:", inventory_number)

    # Start the file with the disclaimer
    text_lines = [DISCLAIMER]
    for f in sorted(os.listdir(folder_path)):
        file_name = f.split("/")[-1]

        text_lines += [f"\n#+ ---\n#+ {file_name}\n#+ ---\n"]
        text_lines += get_text_from_xml(os.path.join(folder_path, f))

    # Write the text to a file
    with open(f"txt/{inventory_number}.txt", "w") as f:
        for line in text_lines:
            f.write(line)
            f.write("\n")


def main(htr_folder):
    filepaths = [os.path.join(htr_folder, f) for f in os.listdir(htr_folder)]

    # with multiprocessing.Pool(os.cpu_count() - 2) as pool:
    with multiprocessing.Pool(10) as pool:
        pool.map(process_folder, filepaths)


if __name__ == "__main__":
    FOLDER = "pagexml"

    main(htr_folder=FOLDER)
