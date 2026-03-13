import numpy as np
import cv2
# import pyautogui
import mss
from PIL import Image

from PlatformOperator import PlatformOperator

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

MONITOR_ROI = {"top": 100, "left": 100, "width": 2880, "height": 2048} # Update after dragging window!

class AutomationProtocol:
    def __init__(self, platformOperator : PlatformOperator = None):
        if platformOperator is None:
            self.platformOperator = PlatformOperator()
        else:
            self.platformOperator = platformOperator

        self.points = []
        self.planeCoeffs = ()

    

    # --- 3-POINT PLANE FIT LOGIC ---
    def calibrate_plane(self):
        logger.debug("---Executing 3-POINT FOCUS ROUTINE ---")
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
        
        self.points = tuple(points)
        self.planeCoeffs = (Planar_A, Planar_B, Planar_C)
        logger.debug(f"Plane Calculated successfully: {self.planeCoeffs}")
        

    # --- Grid Search Loop ---
    def run_scan(self):
        (A, B, C) = self.planeCoeffs
        (p1, p2, p3) = self.points

        x_fov_step = 300
        y_fov_step = 250

        x_left = p1[0]
        # conservative bounding with min, and max to pick the smallest region (may result in minor desired cropping)
        x_right = max(p2[0], p3[0])
        y_top = min(p1[1], p2[1])
        y_bottom = p3[1]

        # start at top-left going right
        x_cur, y_cur, x_dir, y_dir = x_left, y_top, -1, -1

        with mss.mss() as sct:
            while (y_cur <= y_top and y_cur >= y_bottom) or x_dir == -1:
                while (x_cur >= x_right and x_cur <= x_left):
                    # 1. CALCULATE Z
                    target_z = int(A * x_cur + B * y_cur + C)
                    target_point = (x_cur, y_cur, target_z)
                    # 2. MOVE
                    self.platformOperator.synch_go_to_xyz(target_point)
                    
                    # 3. GRAB
                    screenshot = sct.grab(MONITOR_ROI)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                    # img = np.array(screenshot)
                    # img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # 4. INFERENCE (Placeholder for MaskTerial)
                    # is_flake = model.predict(img_bgr)
                    is_flake = False # Replace with real ML call
                    
                    if is_flake:
                        print(f"Flake at {x},{y}!")
                        # 5. TRIGGER NIKON SAVE
                        pyautogui.press('f5')
                        time.sleep(1.0) # Wait for disk write

                    # increment position
                    x_cur += x_fov_step * x_dir

                # next row go backwards in x
                x_dir = -x_dir
                x_cur += x_fov_step * x_dir 
                y_cur += y_fov_step * y_dir
            
            logger.info(f"Ended search @ {self.platformOperator.get_stage_xyz()}")

            # img.show()
