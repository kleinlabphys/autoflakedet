import numpy as np
import cv2
import mss
from PIL import Image
from pathlib import Path
import os
from datetime import datetime

from PlatformOperator import PlatformOperator
from FlakeDetector import FlakeDetector, save_detection_data, load_detection_data
from ObjectiveControl import run_vbs_script
from utility_fns import plot_detected_flakes

import tkinter as tk
from tkinter import filedialog
import time
# import pyautogui

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

MONITOR_ROI = {"top": 150, "left": 184, "width": 2644, "height": 1880} # Image Dimensions when displayed in full screen at 92%

seg_dir = r"C:\Users\2DFab\Documents\Software\autoflakedet\model_training\trained_models\segmentation\thinhbn_150ms_segmenter"
class_dir = r"C:\Users\2DFab\Documents\Software\autoflakedet\model_training\trained_models\classifiers\thin_hBN_150ms_classifier"

PARENT_DIR = Path(__file__).resolve().parent
SWITCH_TO_OBJECTIVE = os.path.join(PARENT_DIR, "VBS_scripts/SwitchToObjective.vbs")

class AutomationProtocol:
    def __init__(self, platformOperator : PlatformOperator = None):
        if platformOperator is None:
            self.platformOperator = PlatformOperator()
        else:
            self.platformOperator = platformOperator

        self.chipsPoints = []
        self.chipsPlaneCoeffs = []
        self.flakeDetector = FlakeDetector(seg_dir, class_dir, size_threshold=1000)
        self.chipsDetectedSpots = []
        self.chipsDimensions = []

    def set_microscope_objective(self, magnification_string):
        run_vbs_script(SWITCH_TO_OBJECTIVE, "20x")

    # --- 3-POINT PLANE FIT LOGIC ---
    def calibrate_planes(self):
        addMoreChips = True
        logger.debug("---Executing 3-POINT FOCUS ROUTINE ---")

        while addMoreChips:
            points = []
            labels = ["BOTTOM-RIGHT", "TOP-RIGHT", "TOP-LEFT"]
            
            for label in labels:
                input(f"Move the stage to {label} of the wafer or scanning region. Now focus camera with fine scroll wheel (or motorized z-control) ONLY. Press ENTER when ready.")
                # Query position from Stage
                position = self.platformOperator.get_stage_xyz()
                points.append(position)
                logger.info(f"Recorded {label} @ {position}")
            
            points.reverse() # start at top left

            assert(points[0][0] > points[1][0] and points[0][0] > points[2][0]), "Top-left is not left of top-right and bottom-right"
            assert(points[2][1] < points[1][1] and points[2][1] < points[0][1]), "Bottom right is not below top-right and top-left"
            # TODO: wrap asserts in handle to request user to retry boundary calibration

            # Solve for Plane: Z = Ax + By + C
            # We have 3 points: (x1,y1,z1), (x2,y2,z2), (x3,y3,z3)
            p1, p2, p3 = np.array(points[0]), np.array(points[1]), np.array(points[2])
            v1 = p2 - p1
            v2 = p3 - p1
            # Cross product to find normal vector (a, b, c) of plane
            normal = np.cross(v1, v2)
            a, b, c = normal
            d = -np.dot(normal, p1)
            
            # Plane equation: ax + by + cz + d = 0  =>  z = -(a/c)x - (b/c)y - (d/c)
            # So A = -a/c, B = -b/c, C = -d/c
            Planar_A = -a / c
            Planar_B = -b / c
            Planar_C = -d / c
            
            self.chipsPoints.append(tuple(points))
            self.chipsPlaneCoeffs.append((Planar_A, Planar_B, Planar_C))
            logger.debug(f"Plane Calculated successfully: {self.chipsPlaneCoeffs[-1]}")
        
            addChipsRequest = "Are you done? Press Enter to add another chip. Type Y if done: "
            addMoreChips = input(addChipsRequest) in ("N", "n", "")


    def run_scans(self):
        numChips = len(self.chipsPoints)
        for i, (planeCoeffs, points) in enumerate(zip(self.chipsPlaneCoeffs, self.chipsPoints)):
            logger.info(f"Now scanning through chip {i + 1}")
            self.run_scan(planeCoeffs, points, i + 1)
        logger.info(f"Finished scanning {len(self.chipsPoints)} chips")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detectionPointsSaveFile = os.path.join(PARENT_DIR, "flakeDetections", f"detections_at_{timestamp}_on_{numChips}_chips.txt")
        save_detection_data(detectionPointsSaveFile, self.chipsDetectedSpots, self.chipsDimensions)
        logger.info(f"Saved flake detection locations to {detectionPointsSaveFile}")
    
    def show_detections(self):
        start_folder = os.path.join(PARENT_DIR, "flakeDetections")
        logger.info("Load a previous run or the current run of saved detections.")
        root = tk.Tk()
        root.withdraw()
        root.update()
        root.attributes('-topmost', True)

        file_path = filedialog.askopenfilename(
            initialdir=start_folder,
            title="Select a flake detection data text file for displaying a grid view",
            filetypes=[("Text files", "*.txt")]
        )

        if file_path in ("", None):
            logger.info("No detection data selected. Skipping display.")
            return

        flake_points, chip_dims = load_detection_data(file_path)

        for cIdx, (fp, (cw, ch)) in enumerate(zip(flake_points, chip_dims)):
            plot_detected_flakes(fp, cw, ch, chipIdx=cIdx)

    # --- Grid Search Loop ---
    def run_scan(self, planeCoeffs, points, chipIdx):
        (A, B, C) = planeCoeffs
        (p1, p2, p3) = points

        x_fov_step = 850
        y_fov_step = 700

        x_left = p1[0]
        # conservative bounding with min, and max to pick the smallest region (may result in minor desired cropping)
        x_right = max(p2[0], p3[0])
        y_top = min(p1[1], p2[1])
        y_bottom = p3[1]
        chipWidth = (x_left - x_right)
        chipHeight = (y_top - y_bottom)

        # start at top-left going right
        x_cur, y_cur, x_dir, y_dir = x_left, y_top, -1, -1
        img_array, img_bgr = None, None
        detectedSpots = []

        with mss.mss() as sct:
            while (y_cur <= y_top and y_cur >= y_bottom) or x_dir == -1:
                while (x_cur >= x_right and x_cur <= x_left):
                    # 1. CALCULATE Z
                    target_z = int(A * x_cur + B * y_cur + C)
                    target_point = (x_cur, y_cur, target_z)
                    # 2. MOVE
                    self.platformOperator.synch_go_to_xyz(target_point)
                    # 3. EXPOSURE FOCUS
                    time.sleep(0.4)
                    # 4. GRAB
                    screenshot = sct.grab(MONITOR_ROI)

                    # Some helpful code to display information if needed to rescale
                    # img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    # img.show()
                    # input("Waiting to cycle")
                    # time.sleep(3)
                    # x, y = pyautogui.position()
                    # print(f"Mouse at: ({x}, {y})")
                    # input("waiting 2")

                    img_array = np.array(screenshot)
                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
                    is_flake = self.flakeDetector.scan_image_for_flakes(img_bgr) # TODO: make this call parallel
                    
                    if is_flake:
                        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                        img.show()
                        localSpot = ((x_cur - x_right), (y_cur - y_bottom))
                        detectedSpots.append(localSpot)
                        x_proportion = localSpot[0] / chipWidth
                        y_proportion = localSpot[1] / chipHeight
                        logger.info(f"Flake locally at {x_proportion * 100}% of the X bounds, {y_proportion * 100}% of the Y bounds!")

                    # increment position
                    x_cur += x_fov_step * x_dir

                # next row go backwards in x
                x_dir = -x_dir
                x_cur += x_fov_step * x_dir 
                y_cur += y_fov_step * y_dir
            
            self.chipsDetectedSpots.append(detectedSpots)
            self.chipsDimensions.append((chipWidth, chipHeight))
            logger.info(f"Ended search on chip {chipIdx} @ {self.platformOperator.get_stage_xyz()}")

