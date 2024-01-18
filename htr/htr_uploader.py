"""
Upload new HTR PageXML files to the TextRepo.

1. Add a new file (v2 transcription) to an existing document (scan level)
2. Update metadata to include e-depot identifier NA. Internally we stick to the filename (d.d. 2022) as external identifier.

Useful API calls:
    * https://globalise.tt.di.huc.knaw.nl/textrepo/task/find/NL-HaNA_1.04.02_1053_0001/document/metadata
    * https://globalise.tt.di.huc.knaw.nl/textrepo/rest/documents/d38ce514-e038-4f7c-aca5-a687b275c0e0/files
    * https://globalise.tt.di.huc.knaw.nl/textrepo/rest/files/7e0a9c15-9022-4116-a8d0-475e78bf47a3/versions

"""
import os
import json
import multiprocessing
import xml.etree.ElementTree as ET

import time

from dotenv import load_dotenv
from textrepo.client import TextRepoClient

# read from .env file
load_dotenv()
TEXTREPO_API_URL = os.getenv("TEXTREPO_API_URL", "")
TEXTREPO_API_KEY = os.getenv("TEXTREPO_API_KEY", "")

with open("inventory2uuid.json") as f:
    inventory2uuid = json.load(f)

client = TextRepoClient(
    base_uri=TEXTREPO_API_URL,
    verbose=False,
    api_key=TEXTREPO_API_KEY,
)


def get_edepot_id(contents: str) -> str:
    """
    Get the edepot identifier from the PageXML file.

    The identifier (a uuid)) is stored in the Metadata
    element as 'externalRef' attribute.

    Example:
        ```xml
        <?xml version="1.0" encoding="UTF-8"?>
        <PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15">
        <Metadata externalRef="3f884222-eb56-4cd1-b79f-e61aa1ea883d">
        ```

    Args:
        contents (str): Contents of the PageXML file

    Returns:
        str: The edepot identifier (uuid)
    """
    tree = ET.fromstring(contents)

    NS = "{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}"
    edepot_id = tree.find(f"{NS}Metadata").get("externalRef")

    return edepot_id


def upload_file(external_id: str, contents: str):
    version_info = client.import_version(
        external_id=external_id,
        type_name="pagexml",
        contents=contents,
        allow_new_document=True,
        as_latest_version=False,  # doet dit wat?
    )

    print(version_info)


def add_metadata(document_uuid, metadata: dict):
    for key, value in metadata.items():
        client.set_document_metadata(document_uuid, key, value)


def read_file(filepath: str) -> tuple[str, str]:
    with open(filepath, "r") as f:
        content = f.read()
        edepot_id = get_edepot_id(content)

    return content, edepot_id


def process_file(filepath: str, base_filename: str):
    """
    Process one PageXML file (upload + metadata).

    Args:
        filepath (str): Path to the PageXML file
        base_filename (str): Filename without extension (also external_identifier)
    """
    print(f"Processing {base_filename}")

    # NL-HaNA_1.04.02_1053_0001
    inventory_number = base_filename.split("_")[2]

    content, edepot_id = read_file(filepath)

    # get document identifier
    print(f"Finding metadata for document {base_filename}")
    try:
        document_uuid = client.read_document_by_external_id(external_uid=base_filename)
    except Exception as e:
        print(f"Document retrieval error for {base_filename}: {e}")
        time.sleep(5)
        return None, filepath

    # first upload the new version
    print(f"Uploading new version for {base_filename}")

    try:
        upload_file(
            external_id=base_filename,
            contents=content,
        )
    except Exception as e:
        print(f"Upload failed for {base_filename}: {e}")
        time.sleep(5)
        return None, filepath

    # change the scan_url
    try:
        _, document_metadata = client.find_document_metadata(external_id=base_filename)
    except Exception as e:
        print(f"Metadata retrieval error for {base_filename}: {e}")
        time.sleep(5)
        return None, filepath

    scan_url = document_metadata.get("scan_url")

    if scan_url:
        service_info_url = scan_url.replace("/iip/", "/iipsrv?IIIF=/")
        if service_info_url.endswith(".jp2"):
            service_info_url = service_info_url + "/info.json"
    else:
        try:
            inventory_uuid = inventory2uuid[inventory_number]
        except Exception as e:
            print(f"Inventory number retrieval error for {base_filename}: {e}")
            return None, filepath
        inventory_uuid = inventory_uuid.replace("-", "")

        inventory_uuid_chunks = [
            inventory_uuid[i : i + 2] for i in range(0, len(inventory_uuid), 2)
        ]

        service_info_url = f"https://service.archief.nl/iipsrv?IIIF=/{'/'.join(inventory_uuid_chunks)}/{edepot_id}.jp2/info.json"

    # then add the metadata, including the more permanent identifier to the document
    print(f"Adding metadata for {base_filename}")
    try:
        add_metadata(
            document_uuid.id,
            {
                "inventory_number": inventory_number,
                "edepot_id": edepot_id,
                "scan_url": service_info_url,
            },
        )
    except Exception as e:
        print(f"Metadata update failed for {base_filename}: {e}")
        time.sleep(5)
        return None, filepath

    return filepath, None


def main(pagexml_folder: str, chunksize: int = 1000):
    files_to_process = []

    with open("upload_success.txt", "r") as f:
        succesfully_uploaded_files = set(f.read().splitlines())

    # For every xml file
    for root, _, files in os.walk(pagexml_folder):
        for file in sorted(files):
            if not file.endswith(".xml") and "NL-HaNA" not in file:
                continue

            filepath = os.path.join(root, file)
            base_filename, _ = os.path.splitext(file)

            if filepath in succesfully_uploaded_files:
                print(f"Skipping {base_filename}")
                continue
            files_to_process.append((filepath, base_filename))

    # Chunk it up
    for i in range(0, len(files_to_process), chunksize):
        print(f"Processing files {i} to {i+chunksize}")

        with multiprocessing.Pool(10) as pool:
            results = pool.starmap(process_file, files_to_process[i : i + chunksize])

        success, errors = zip(*results)

        with open("upload_success.txt", "a") as f:
            for s in success:
                if s:
                    f.write(s + "\n")

        with open("upload_errors.txt", "a") as f:
            for e in errors:
                if e:
                    f.write(e + "\n")


def fix_missing(filepath: str):
    with open(filepath, "r") as f:
        document_paths = f.read().splitlines()
        document_names = [i.split("/")[-1].replace(".xml", "") for i in document_paths]

    for d_path, d_name in zip(document_paths, document_names):
        inventory_number = d_name.split("_")[2]
        inventory_number = {"9524I": "9524A", "9524II": "9524B"}.get(
            inventory_number, inventory_number
        )

        inventory_uuid = inventory2uuid[inventory_number]
        inventory_uuid = inventory_uuid.replace("-", "")

        inventory_uuid_chunks = [
            inventory_uuid[i : i + 2] for i in range(0, len(inventory_uuid), 2)
        ]

        edepot_id = get_edepot_id(open(d_path).read())

        service_info_url = (
            f"https://service.archief.nl/iipsrv?IIIF=/{inventory_uuid_chunks}/"
            + f"{edepot_id}.jp2/info.json"
        )

        # add metadata
        print(f"Adding metadata for {d_name}")
        try:
            add_metadata(
                client.read_document_by_external_id(external_uid=d_name).id,
                {
                    "inventory_number": d_name.split("_")[2],
                    "edepot_id": edepot_id,
                    "scan_url": service_info_url,
                },
            )
        except Exception as e:
            print(f"Metadata update failed for {d_name}: {e}")
            continue


if __name__ == "__main__":
    FOLDER = "/media/leon/HDE00551/GLOBALISE/HTR/2023_09/pagexml/"
    main(FOLDER)

    # Missing
    fix_missing("upload_errors.txt")
