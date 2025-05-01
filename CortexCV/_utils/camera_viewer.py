import cv2
from .._core._core_tools import osDetector
from .._core.engines import engine_loader
from .._utils import _ANSI

def getCameraview():
    os = osDetector.detectOS()

    if os.lower() == "windows":
        cameraView = engine_loader.get_camera_input() # initiate the engines and the function to get the frames

    else:
        cameraView = cv2.VideoCapture(0)
        if not cameraView.isOpened():
            raise Exception(f"{_ANSI.red()}[!] Camera is not available{_ANSI.reset()}")
    
    return cameraView
