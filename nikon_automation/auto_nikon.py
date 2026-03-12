import serial
import time
import mss
import numpy as np
import cv2
import pyautogui
import logging

# modules for stage control
from ctypes import WinDLL, create_string_buffer
import os
import sys


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

COM_PORT = '4'  # Check Device Manager for Prior Stage
MONITOR_ROI = {"top": 100, "left": 100, "width": 2880, "height": 2048} # Update after dragging window!
prior_sdk_buffer_length = 1000
PRIOR_SCIENTIFIC_SDK_DLL_PATH = "C:\\Program Files\\Prior Scientific\\PriorSDK 2.0.0\\x64\\PriorScientificSDK.dll"

def link_prior_sdk_module(path):
    if os.path.exists(path):
        SDKPrior = WinDLL(path)
    else:
        raise RuntimeError("SDKPrior DLL could not be loaded. Check to see if it exists in the path provided")
    
    return SDKPrior

class PriorControl:
    def __init__(self):
        self.SDKPrior = link_prior_sdk_module(PRIOR_SCIENTIFIC_SDK_DLL_PATH)
        self.output_buffer = create_string_buffer(prior_sdk_buffer_length)
        self.sessionID = self.SDKPrior.PriorScientificSDK_OpenNewSession()
        init_status = self.SDKPrior.PriorScientificSDK_Initialise()
        if init_status:
            raise RuntimeError(f"Error initialising Prior Software control {init_status}")
        
        version_status = self.SDKPrior.PriorScientificSDK_Version(self.output_buffer)
        logger.debug(f"dll version api ret={version_status}, version={self.output_buffer.value.decode()}")

        if self.sessionID < 0:
            logger.error("Error getting session id:")

    def send_prior_cmd(self, cmd_str, flush_immediately=False, log_level=logging.DEBUG):
        cmd_status = self.SDKPrior.PriorScientificSDK_cmd(
            self.sessionID, create_string_buffer(cmd_str.encode()), self.output_buffer
        )

        if flush_immediately:
            if cmd_status:
                logger.error(f"Error executing {cmd_str} with status code: {cmd_status}")
            else:
                logger.log(log_level, f"OK {self.output_buffer.value.decode()}")
        else:
            return cmd_status, self.output_buffer.value.decode()


## TODO: Close and open Nikon software at start to have window placed conveniently for capture


class AutomationProtocol:
    def __init__(self, priorController : PriorControl = None):
        if priorController is None:
            self.priorController = PriorControl()

    # --- 3-POINT PLANE FIT LOGIC ---
    def calibrate_plane(self):
        logger.debug("---Executing 3-POINT FOCUS ROUTINE ---")
        points = []
        labels = ["TOP-LEFT", "TOP-RIGHT", "BOTTOM-RIGHT"]
        
        for label in labels:
            input(f"Move the stage to {label} of the wafer or scanning region. Then focus screen view manually with course knob. Press ENTER when ready.")
            # Query position from Stage
            code_status, pos_str = self.priorController.send_prior_cmd("controller.stage.position.get")

            x, y, z = map(int, pos_str.split(','))
            points.append((x, y, z))
            logger.info(f"Recorded {label}: {x}, {y}, {z}")

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
        
        logger.debug("Plane Calculated successfully")
        return Planar_A, Planar_B, Planar_C

    # --- MAIN BOT ---
    def run_scan(self, A, B, C):
        # Define your grid here (e.g., 0 to 20000 microns)
        # This is a dummy grid for example
        x_range = range(0, 20000, 300) # 300um steps
        y_range = range(0, 20000, 200) # 200um steps
        
        with mss.mss() as sct:
            for x in x_range:
                for y in y_range:
                    # 1. CALCULATE Z
                    target_z = int(A * x + B * y + C)
                    
                    # 2. MOVE
                    self.priorController.send_prior_cmd(f"G,{x},{y},{target_z}") # TODO: change up with actual go to command from manual
                    time.sleep(0.1) # Settle
                    
                    # 3. GRAB
                    screenshot = sct.grab(MONITOR_ROI)
                    img = np.array(screenshot)
                    img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # 4. INFERENCE (Placeholder for MaskTerial)
                    # is_flake = model.predict(img_bgr)
                    is_flake = False # Replace with real ML call
                    
                    if is_flake:
                        print(f"Flake at {x},{y}!")
                        # 5. TRIGGER NIKON SAVE
                        pyautogui.press('f5')
                        time.sleep(1.0) # Wait for disk write

def main():
    priorController = PriorControl()
    # Ensure connection to Stage control device is solid first
    priorController.send_prior_cmd("dll.apitest 33 goodresponse", flush_immediately=True)
    priorController.send_prior_cmd("dll.apitest -300 stillgoodresponse", flush_immediately=True)

    # Connect to prior device over usb
    priorController.send_prior_cmd(f"controller.connect {COM_PORT}", flush_immediately=True, log_level=logging.INFO)

    # Run automation
    automater = AutomationProtocol(priorController)
    automater.calibrate_plane()

# --- EXECUTION ---
if __name__ == "__main__":
    main()
    # A, B, C = calibrate_plane()
    # run_scan(A, B, C)


