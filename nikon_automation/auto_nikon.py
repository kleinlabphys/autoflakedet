import logging

from AutomationProtocol import AutomationProtocol

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

COM_PORT = '4'  # Check Device Manager for Prior Stage

## TODO: Close and open Nikon software at start to have window placed conveniently for capture

def main():
    # Initialize
    automator = AutomationProtocol()
    automator.platformOperator.connect_to_device(COM_PORT)

    # Run automation
    automator.calibrate_plane()
    automator.run_scan()

    # Shutdown
    automator.platformOperator.disconnect_and_close_session(COM_PORT)
    

# --- EXECUTION ---
if __name__ == "__main__":
    main()
    logger.info("Automation Complete :)")


