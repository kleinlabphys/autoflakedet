import subprocess
import os

def run_vbs_script(vbs_file, args=None):
    if args is None:
        args = []

    vbs_file = os.path.abspath(vbs_file)

    result = subprocess.run(
        ["cscript", "//nologo", vbs_file] + args,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"VBScript failed:\n{result.stderr}")

    return result.stdout

# example forward nosepiece program
# run_vbs_script('C:\\Program Files\\Nikon\\LV-Series\\Samples\\Scripts\\ForwardNosepiece.vbs')