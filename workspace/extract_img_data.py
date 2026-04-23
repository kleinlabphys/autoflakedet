# this script is to extract the meta data of images, found under EXIF when you do CMD + I on mac
# issue I ran into is that not all images have EXIF data and even then

from PIL import Image
from PIL.ExifTags import TAGS
from PIL.TiffTags import TAGS as TIFF_TAGS

def extract_lens_data(image_path):
    """"
    Extract lens data from an image, looking for both JPEG and TIFF in case
    file is saved as TIFF (Tag_V2)
    """
    try:
        with Image.open(image_path) as img: # extracts he raw EXIF data
            # test function 1
            print('Format:', img.format)

            exif = img.getexif()
            print('Raw Exif:', exif)
            # end of test function

            # begining of new test function
            print('img.info:', img.info)

            if hasattr(img, 'applist'):
                print('applist:', img.applist)
            # end of new test function

            full_data = {}

            # if JPEG (i.e., EXIF data)
            if img.format == 'JPEG':
                exif = img.getexif()
                if exif:
                    for tag_id, value in exif.items(): # root tags (Make, model)
                        full_data[TAGS.get(tag_id, tag_id)] = value

                    # sub IFD tags: (LensModel, FocalLength)
                    exif_sub_ifd = exif.get_ifd(0x8769)
                    for tag_id, value in exif_sub_ifd.items():
                        full_data[TAGS.get(tag_id, tag_id)] = value

            # case where we have TIFF info (Tag_V2)
            elif img.format == 'TIFF':
                if hasattr(img, 'tag_v2'):
                    for tag_id, value in img.tag_v2.items():
                        tag_name = TIFF_TAGS.get(tag_id, tag_id)
                        full_data[tag_name] = value

            # if neither  tiff nor EXIF is found
            if not full_data:
                print(f'No metadata found for {img.format} file')
                return None

            # for readability
            results = {
                'Camera': f"{full_data.get('Make', '')}{full_data.get('Model', '')}".strip() or 'Unknown',
                'Lens Model': full_data.get('LensModel', full_data.get('Model', 'Unknown Lens')),
                'Focal Length': full_data.get('FocalLength', 'Unknown'),
                'Image Description': full_data.get('ImageDescription', 'Not Found'),
            }

            return results

    except FileNotFoundError:
        print('Error: File not found. Check filename.')
        return None

    except Exception as e:
        print(f'Error Processing {e}')
        return None

if __name__ == '__main__':
    file_name = r'graphene_20x_samples/chip3_f3_20x.jpg'
    data = extract_lens_data(file_name)

    if isinstance(data, dict):
        print(f"{'Field':<20} | {'Value'}")
        print('-' * 40)
        for key, value in data.items():
            print(key, ':', value)
            print(f'{key:<20} | {value}')

    else:
        print('Could not retrieve data.')

