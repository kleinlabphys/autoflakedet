# modules for stage control
from ctypes import WinDLL, create_string_buffer
import os, time

from PriorCleanup import PriorCleanup

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

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
        init_status = self.SDKPrior.PriorScientificSDK_Initialise()

        if init_status:
            raise RuntimeError(f"Error initialising Prior Software control {init_status}")

        version_status = self.SDKPrior.PriorScientificSDK_Version(self.output_buffer)
        logger.debug(f"dll version api ret={version_status}, version={self.output_buffer.value.decode()}")
        self.sessionID = self.SDKPrior.PriorScientificSDK_OpenNewSession()

        if self.sessionID < 0:
            raise RuntimeError("Error getting session id:")

    def send_prior_cmd(self, cmd_str, flush_immediately=False, log_level=logging.DEBUG, expected_status=0):
        cmd_status = self.SDKPrior.PriorScientificSDK_cmd(
            self.sessionID, create_string_buffer(cmd_str.encode()), self.output_buffer
        )

        if type(expected_status) == int and cmd_status != expected_status or type(expected_status) == list and cmd_status not in expected_status:
            logger.error(f"Error executing {cmd_str} with status code: {cmd_status}. Expected {expected_status}")
            return False
        elif flush_immediately:
            logger.log(log_level, f"Executed '{cmd_str}' OK. Recieved data: {self.output_buffer.value.decode()}")
            return True
        else:
            return cmd_status, self.output_buffer.value.decode()
        
    def connect_to_device(self, port_number='4'):
        # Ensure connection to Stage control device is solid first
        self.send_prior_cmd("dll.apitest 33 goodresponse", flush_immediately=True, expected_status=33)
        self.send_prior_cmd("dll.apitest -300 stillgoodresponse", flush_immediately=True, expected_status=-300)

        # Connect to prior device over usb TODO: add retry logic
        connect_result = self.send_prior_cmd(f"controller.connect {port_number}", flush_immediately=True, log_level=logging.INFO)
        return connect_result

    def disconnect_and_close_session(self, port_num):
        self.send_prior_cmd("controller.disconnect", flush_immediately=True, log_level=logging.INFO)
        ses_close_status = self.SDKPrior.PriorScientificSDK_CloseSession(self.sessionID)
        if ses_close_status:
            logger.error("Encountered a problem with closing PriorSDK session")
        
        # Hack to restore Prior control for NIS elements
        PriorCleanup.run_prior_test_cleanup(port_num)