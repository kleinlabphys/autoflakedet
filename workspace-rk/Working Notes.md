
**Launching labelme done via powershell**

`python -m labelme`

Labelme Polygon to RLE Conversion

This guide explains how to convert Labelme polygon annotations (.json) into RLE (Run-Length Encoding) masks, which are commonly required for COCO, Detectron2, Mask R-CNN, and other segmentation frameworks.

Overview

Input: Labelme JSON files with polygon annotations

Output: COCO-style RLE masks

Supports:

Single polygons

Multiple polygons per object using group_id (instance segmentation)

Dependencies

Install the required Python packages:

pip install labelme pycocotools numpy pillow

Labelme Annotation Format

Each annotation in Labelme contains:

label: class name (e.g. person)

points: polygon vertices

shape_type: should be "polygon"

group_id (optional): used to group multiple polygons into one instance

Polygon → RLE Conversion (Basic)

This converts each polygon into an individual RLE mask.

Code
import json
import numpy as np
from labelme import utils
from pycocotools import mask as maskUtils


def labelme_polygon_to_rle(json_path):
    with open(json_path) as f:
        data = json.load(f)

    height = data["imageHeight"]
    width = data["imageWidth"]

    rles = []

    for shape in data["shapes"]:
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

        rles.append({
            "label": label,
            "rle": rle
        })

    return rles

Handling group_id (Instance Segmentation)

If your Labelme annotations use group_id, all polygons with the same (label, group_id) must be merged into a single mask before encoding.

This is required for:

Instance segmentation

Panoptic segmentation

Occluded or multi-part objects

Grouped Polygon → RLE Conversion
import json
import numpy as np
from collections import defaultdict
from labelme import utils
from pycocotools import mask as maskUtils


def labelme_grouped_rle(json_path):
    with open(json_path) as f:
        data = json.load(f)

    height = data["imageHeight"]
    width = data["imageWidth"]

    groups = defaultdict(list)

    # Group shapes by (label, group_id)
    for shape in data["shapes"]:
        if shape["shape_type"] != "polygon":
            continue
        key = (shape["label"], shape.get("group_id"))
        groups[key].append(shape)

    rles = []

    for (label, group_id), shapes in groups.items():
        combined_mask = np.zeros((height, width), dtype=np.uint8)

        for shape in shapes:
            mask = utils.shape_to_mask(
                img_shape=(height, width),
                points=shape["points"],
                shape_type="polygon"
            )
            combined_mask |= mask

        rle = maskUtils.encode(
            np.asfortranarray(combined_mask)
        )
        rle["counts"] = rle["counts"].decode("utf-8")

        rles.append({
            "label": label,
            "group_id": group_id,
            "rle": rle
        })

    return rles

Output Format

Each RLE follows the COCO specification:

{
  "size": [height, width],
  "counts": "encoded_string"
}


Example:

{
  "label": "person",
  "group_id": 1,
  "rle": {
    "size": [720, 1280],
    "counts": "f`1:0O2N2..."
  }
}

Using RLE in COCO Annotations

COCO expects RLE under the segmentation field:

{
  "segmentation": {
    "counts": "...",
    "size": [H, W]
  },
  "category_id": 1,
  "iscrowd": 0
}


You will still need to add:

image_id

category_id (map from label name)

bbox

area

Common Pitfalls

❌ Not using np.asfortranarray before encoding

❌ Encoding boolean masks instead of uint8

❌ Forgetting to merge polygons with the same group_id

❌ Leaving counts as bytes (must be UTF-8 string)

Notes

Label List → defines class

group_id → defines instance

Ignore group_id if doing semantic segmentation only




------


✅ Recommended: from the binary mask

Once you already have the polygon → mask:

import numpy as np

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



------



✅ Correct way: sum of mask pixels
def mask_to_area(mask):
    return int(mask.sum())


Why:

Exact match to RLE

Handles merged shapes

Same value COCO evaluation uses