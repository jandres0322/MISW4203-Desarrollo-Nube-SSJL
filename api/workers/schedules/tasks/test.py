import subprocess
import importlib



path = "../../../batch/convert_video.sh"
p = subprocess.Popen(f"sh {path} Juan Pedro", shell=True)

