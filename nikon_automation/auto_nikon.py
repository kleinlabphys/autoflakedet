import serial
import time
import mss
import numpy as np
import cv2
import pyautogui

# --- CONFIGURATION (STUDENT FILLS THIS) ---
COM_PORT = 'COM4'  # Check Device Manager for Prior Stage
MONITOR_ROI = {"top": 100, "left": 100, "width": 2880, "height": 2048} # Update after dragging window!

# --- HARDWARE SETUP ---
try:
    stage = serial.Serial(COM_PORT, 9600, timeout=1)
except:
    print(f"Error: Could not open {COM_PORT}. Is the Stage on?")
    exit()

def send_prior_cmd(cmd_str):
    """Sends a command to Prior controller and waits for completion."""
    stage.write(f"{cmd_str}\r".encode())
    # Prior controllers usually reply with 'R' or '0' when done.
    # Simple blocking wait:
    while True:
        response = stage.readline().decode().strip()
        if response == 'R': # 'R' is standard "Ready" response
            break

# --- 3-POINT PLANE FIT LOGIC ---
def calibrate_plane():
    print("--- 3-POINT FOCUS ROUTINE ---")
    points = []
    labels = ["TOP-LEFT", "BOTTOM-RIGHT", "CENTER"]
    
    for label in labels:
        input(f"Move stage to {label} of the wafer. Focus manually on screen. Press ENTER when ready.")
        # Query position from Stage
        stage.write(b"P\r") 
        # Response format usually: "X,Y,Z"
        pos_str = stage.readline().decode().strip() 
        x, y, z = map(int, pos_str.split(','))
        points.append((x, y, z))
        print(f"Recorded {label}: {x}, {y}, {z}")

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
    
    print("Plane Calculated!")
    return Planar_A, Planar_B, Planar_C

# --- MAIN BOT ---
def run_scan(A, B, C):
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
                send_prior_cmd(f"G,{x},{y},{target_z}")
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

# --- EXECUTION ---
if __name__ == "__main__":
    A, B, C = calibrate_plane()
    run_scan(A, B, C)


