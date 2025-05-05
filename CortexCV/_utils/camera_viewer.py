import cv2
from .._core._core_tools import osDetector
from .._core.engines import engine_loader
from .._utils import _ANSI


# The high level interface that will communicate CortexCV engines
# and/or OpenCV to get contnous camera frames 

def getCameraview():
    os = osDetector.detectOS()

    if os.lower() == "windows":
        isEnable = engine_loader.loadDLL()
        if isEnable:
            cameraView = engine_loader.get_camera_input() # initiate the engines and the function to get the frames
        else:
            cameraView = cv2.VideoCapture(0)
            if not cameraView.isOpened():
                raise Exception(f"{_ANSI.red()}[!] Camera is not available{_ANSI.reset()}")

    else:
        cameraView = cv2.VideoCapture(0)
        if not cameraView.isOpened():
            raise Exception(f"{_ANSI.red()}[!] Camera is not available{_ANSI.reset()}")
    
    return cameraView
