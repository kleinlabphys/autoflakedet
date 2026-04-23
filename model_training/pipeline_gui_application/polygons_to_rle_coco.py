import os
import json 
from labelme import utils
from pycocotools import mask as maskUtils
import numpy as np
from pathlib import Path

def create_bulk_coco_annotations_from_polygon_images(labelme_annotation_dir, output_coco_json_file):
    output_coco_json_data = {
        "info": {},
        "licenses": [],
        # "categories": [
        #     {
        #         "supercategory": "foreground",
        #         "id": 1,
        #         "name": "1-Layer"
        #     },
        #     # {
        #     #     "supercategory": "foreground",
        #     #     "id": 2,
        #     #     "name": "2-Layer"
        #     # },
        #     # {
        #     #     "supercategory": "foreground",
        #     #     "id": 3,
        #     #     "name": "3-Layer"
        #     # },
        #     # {
        #     #     "supercategory": "foreground",
        #     #     "id": 4,
        #     #     "name": "4-Layer"
        #     # }
        # ]
    }

    coco_images = []
    images_with_idx = dict()
    cur_image_idx = 0
    cur_polygon_idx = 0
    annotations = []

    input_json_dir = Path(labelme_annotation_dir)
    unscaled_labels = set()
    all_jsons = list(input_json_dir.glob("*.json"))
    num_jsons = len(all_jsons)
    for json_path in all_jsons:
        with open(json_path) as f:
            data = json.load(f)

            image_full_path = os.path.abspath(os.path.join(os.path.dirname(json_path), data["imagePath"]))
            image_file_name = os.path.basename(image_full_path)
            # print(image_file_name, image_full_path)
            if image_file_name not in images_with_idx:
                images_with_idx[image_file_name] = cur_image_idx
                coco_images.append({
                    "file_name": image_file_name,
                    "height": data["imageHeight"],
                    "width": data["imageWidth"],
                    "id": cur_image_idx
                })
                cur_image_idx += 1

            image_id = images_with_idx[image_file_name]
            coco_annotation = labelme_polygons_data_to_coco_annotation(data, image_id, cur_polygon_idx)
            [unscaled_labels.add(annotation["category_id"]) for annotation in coco_annotation]
            annotations += coco_annotation
            cur_polygon_idx += len(data["shapes"])
            yield image_file_name, int((cur_image_idx) / (num_jsons + 1) * 100)
  
    # rescale the annotations to not have gaps
    unscaled_to_scaled_labels = {num: i + 1 for i, num in enumerate(sorted(unscaled_labels))}
    for annotation in annotations:
        annotation["category_id"] = unscaled_to_scaled_labels[annotation["category_id"]]

    output_coco_json_data["categories"] = [
        {
            "supercategory": "foreground",
            "id": id_idx,
            "name": f"{id_idx}-Layer"
        } for id_idx in range(1, len(unscaled_to_scaled_labels) + 1)
    ]

    # include annotations json
    output_coco_json_data["annotations"] = annotations

    # include images jsons
    output_coco_json_data["images"] = coco_images

    with open(output_coco_json_file, "w") as f:
        json.dump(output_coco_json_data, f, indent=4)

    yield None, 100 # progress complete

def mask_to_bbox(mask):
    ys, xs = np.where(mask > 0)

    x_min = xs.min()
    x_max = xs.max()
    y_min = ys.min()
    y_max = ys.max()

    return [
        int(x_min),
        int(y_min),
        int(x_max - x_min + 1),
        int(y_max - y_min + 1)
    ]

def labelme_polygons_data_to_coco_annotation(polygons_data, image_id, start_polygon_idx):
    annotations = []
    height = polygons_data["imageHeight"]
    width = polygons_data["imageWidth"]

    polygon_idx = start_polygon_idx
    for shape in polygons_data["shapes"]:
        if shape["shape_type"] != "polygon":
            continue

        label = shape["label"]
        points = shape["points"]

        # Create binary mask from polygon
        mask = utils.shape_to_mask(
            img_shape=(height, width),
            points=points,
            shape_type="polygon"
        )

        # Convert mask to RLE (Fortran order required)
        rle = maskUtils.encode(
            np.asfortranarray(mask.astype(np.uint8))
        )

        # Convert bytes to string for JSON serialization
        rle["counts"] = rle["counts"].decode("utf-8")

        # Compute area
        area = maskUtils.area(rle).item()

        annotations.append({
            "segmentation": rle,
            "area": area,
            "isCrowd": 0,
            "bbox": mask_to_bbox(mask),
            "category_id": int(label) if label.isdigit() else label,
            "image_id": image_id,
            "id": polygon_idx
        })

        polygon_idx += 1

    return annotations