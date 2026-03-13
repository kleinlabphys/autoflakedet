import subprocess
import pyautogui
import win32gui
import win32con

from utility_fns import wait_until_ready

PRIOR_TEST_PATH = "C:\\Program Files\\Prior Scientific\\Prior Software Pack x64\\Demo\\PriorTest.exe"
PRIOR_WINDOW_CLASS = "WindowsForms10.Window.8.app.0.bb8560_r7_ad1"

class PriorCleanup:
    @classmethod
    @wait_until_ready()
    def wait_for_window_appearance(cls, window_name, window_class=PRIOR_WINDOW_CLASS):
        hwnd = win32gui.FindWindow(window_class, window_name)
        return hwnd

    @classmethod
    def run_prior_test_cleanup(cls, port_num, priortest_path=PRIOR_TEST_PATH):
        # Launch PriorTest window, let it initialize, then close
        proc = subprocess.Popen([priortest_path])
        cls.wait_for_window_appearance("Port Selection")
        pyautogui.typewrite(str(port_num))
        pyautogui.press("enter")
        hwnd = cls.wait_for_window_appearance("Prior Test Control")
    
        # Close the window
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        proc.wait()  # wait for clean exit