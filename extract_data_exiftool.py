import subprocess
import json
import xml.etree.ElementTree as ET

def parse_ome_xml(image_description):
    try:
        root = ET.fromstring(image_description)

        # Namespace handling
        ns = {'ome': 'http://www.openmicroscopy.org/Schemas/OME/2015-01'}

        objective = root.find(".//ome:Objective[@Model]", ns)
        if objective is not None:
            return {
                "Objective Model": objective.attrib.get("Model"),
                "Nominal Magnification": objective.attrib.get("NominalMagnification"),
                "Lens NA": objective.attrib.get("LensNA"),
            }

    except Exception as e:
        print(f"OME XML parsing error:{e}")

    return {}


def extract_lens_data_exif(image_path):
    """
    extract lens data using exiftool which is better
    """

    try:
        # calling exif tool and getting JSON output
        result = subprocess.run(
            ['exiftool', '-json', image_path],
            capture_output=True,
            text = True
        )

        if result.returncode != 0:
            print('ExifTool error:', result.stderr)
            return None

        metadata = json.loads(result.stdout)[0]

        if 'ImageDescription' in metadata: # for microscope TIFF
            ome_data = parse_ome_xml(metadata['ImageDescription'])
            return ome_data or None

        return None

    except Exception as e:
        print(f'Error processing file: {e}')
        return None

if __name__ == '__main__':
    file_name = r'graphene_20x_samples/c3_f1_20x.tif'

    data = extract_lens_data_exif(file_name)

    if data:
        print(f"{'Field':<25} | Value")
        print('-' * 50)
        for key, value in data.items():
            print(f'{key:<20} | {value}')

    else:
        print('Could not retrieve lens data.')
