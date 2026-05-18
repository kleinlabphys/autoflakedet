import os
import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
from tkinter import filedialog

from typing import List, Tuple
from pathlib import Path

SEG_MODEL = "M2F"
CLS_MODEL = "AMM"

PP_MODEL = None
PP_MODEL_ROOT = None

SCORE_THRESHOLD = 0.1
MIN_CLASS_OCCUPANCY = 0.5
SIZE_THRESHOLD = 200


from maskterial import MaskTerial, load_models
from maskterial.structures import Flake

def display_results(
    image: np.ndarray,
    flakes: list[Flake],
    colors: list[tuple[int, int, int]] = [
        (255, 0, 0),
        (0, 0, 255),
        (0, 255, 0),
        (0, 255, 255),
        (255, 0, 255),
        (255, 41, 255),
    ],
):
    for flake in flakes:
        mask = flake.mask.astype(np.uint8)
        class_id = int(flake.thickness)

        # Draw outline
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(image, contours, -1, colors[class_id], 2)

        # Get bounding box
        x, y, w, h = cv2.boundingRect(mask)

        # Draw bounding box
        cv2.rectangle(image, (x, y), (x + w, y + h), colors[class_id], 2)

        # Add class label
        label = f"Class {class_id}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2

        # Get text size for background
        (text_width, text_height), baseline = cv2.getTextSize(
            label, font, font_scale, thickness
        )

        # Adjust text position to keep it within bounds
        text_y = y - 5 if y - text_height - 10 >= 0 else y + h + text_height + 5
        bg_y1 = text_y - text_height - 5 if y - text_height - 10 >= 0 else y + h
        bg_y2 = text_y + 5 if y - text_height - 10 >= 0 else y + h + text_height + 10

        # Draw background rectangle for text
        cv2.rectangle(image, (x, bg_y1), (x + text_width, bg_y2), colors[class_id], -1)

        # Draw text
        cv2.putText(
            image, label, (x, text_y), font, font_scale, (255, 255, 255), thickness
        )

    fig, axis = plt.subplots(1, 1, figsize=(12, 12), dpi=100)
    plt.imshow(image[:, :, ::-1])
    plt.axis("off")
    plt.show()

class FlakeDetector:
    def __init__(self, segmentation_model_dir, classifier_model_dir, score_threshold=0.1, min_class_occupancy=0.5, size_threshold=200):

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        segmentation_model, classification_model, postprocessing_model = load_models(
            seg_model_type=SEG_MODEL,
            seg_model_root=segmentation_model_dir,
            cls_model_type=CLS_MODEL,
            cls_model_root=classifier_model_dir,
            pp_model_type=PP_MODEL,
            pp_model_root=PP_MODEL_ROOT,
            device=self.device,
        )
        
        self.predictor = MaskTerial(
            segmentation_model=segmentation_model,
            classification_model=classification_model,
            postprocessing_model=postprocessing_model,
            score_threshold=score_threshold,
            min_class_occupancy=min_class_occupancy,
            size_threshold=size_threshold,
            device=self.device,
        )

    def scan_image_for_flakes(self, image_bytes : np.ndarray, display_success_option=False):
        flakes = self.predictor.predict(image_bytes)

        result = len(flakes) > 0
        if display_success_option and result:
            display_results(image_bytes, flakes)

        return result
    

## Some utilities for flake detection data saving ##
def save_detection_data(
    filename: str,
    A: List[List[Tuple[float, float]]],
    B: List[Tuple[float, float]]
) -> None:
    """
    Writes A and B to a text file.

    Format:
    - One line per pair (A[i], B[i])
    - A[i] encoded as x1,y1;x2,y2;...
    - B[i] encoded as j,k
    - Separated by |

    Example line:
    1.0,2.0;3.0,4.0|5.0,6.0
    """
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w") as f:
        for a_list, (j, k) in zip(A, B):
            a_str = ";".join(f"{x},{y}" for x, y in a_list)
            b_str = f"{j},{k}"
            f.write(f"{a_str}|{b_str}\n")


def load_detection_data(
    filename: str
) -> Tuple[List[List[Tuple[float, float]]], List[Tuple[float, float]]]:
    """
    Reads the file created by save_detection_data() and reconstructs A and B.
    """
    A = []
    B = []

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            a_part, b_part = line.split("|")

            # Decode A[i]
            a_list = []
            if a_part:
                for pair_str in a_part.split(";"):
                    x_str, y_str = pair_str.split(",")
                    a_list.append((float(x_str), float(y_str)))

            # Decode B[i]
            j_str, k_str = b_part.split(",")
            b_tuple = (float(j_str), float(k_str))

            A.append(a_list)
            B.append(b_tuple)

    return A, B

# example usage for testing on samples
if __name__ == "__main__":
    seg_dir = r"C:\Users\2DFab\Documents\Software\autoflakedet\model_training\trained_models\segmentation"
    class_dir = r"C:\Users\2DFab\Documents\Software\autoflakedet\model_training\trained_models\classifiers\thin_hBN_11_images_classifier"
    f = FlakeDetector(seg_dir, class_dir)
    image_to_examine = "some_image"
    print("Keep selecting images for flake detection. Select cancel when finished")
    while image_to_examine:
        image_to_examine = filedialog.askopenfilename(title="Select image for flake detection")
        if image_to_examine:
            contains = f.scan_image_for_flakes(cv2.imread(image_to_examine), display_success_option=True)
            print(contains)
