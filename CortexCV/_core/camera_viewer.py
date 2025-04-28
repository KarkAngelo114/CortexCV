import cv2

def getCameraview():
    cameraView = cv2.VideoCapture(0)
    if not cameraView.isOpened():
        raise Exception("[!] Camera is not available")
    
    return cameraView
