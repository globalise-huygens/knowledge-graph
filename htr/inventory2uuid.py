import json
import lxml.etree as ET


def get_inventory_uuid(xml_filepath):
    tree = ET.parse(xml_filepath)

    files = tree.xpath('//c[@level="file"]')

    inventory2uuid = dict()
    for file in files:
        inventory_number_el = file.xpath("did/unitid[@identifier]")
        if inventory_number_el:
            inventory_number = inventory_number_el[0].text
        else:
            continue

        gaf_uuid_els = file.xpath("did/dao/@href")
        if gaf_uuid_els:
            gaf_uuid = gaf_uuid_els[0].split("/")[-1]

            inventory2uuid[inventory_number] = gaf_uuid

    return inventory2uuid


if __name__ == "__main__":
    inventory2uuid = get_inventory_uuid("1.04.02.xml")

    with open("inventory2uuid.json", "w") as f:
        json.dump(inventory2uuid, f, indent=2)
