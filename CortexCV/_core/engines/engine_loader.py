import ctypes
import ctypes
import numpy as np
import cv2
import platform
import os
from ..._utils import _ANSI

DLL_path = ""

def loadDLL():
    global DLL_path
    arch,_ = platform.architecture()
    DLL = "cortex_engine_64bit.dll" if arch == "64bit" else "cortex_engine_32bit.dll"
    path = os.path.dirname(os.path.abspath(__file__))

    path_to_DLL = os.path.join(path, DLL)

    if not os.path.exists(path_to_DLL):
        isEnable = False
        return isEnable
    else:
        isEnable = True
        DLL_path = path_to_DLL
        print(f"{_ANSI.cyan()}[/] Successfully loaded CortexCV engine {arch} {_ANSI.reset()}")
        return isEnable
        

def get_camera_input():
    # Load the DLL
    global DLL_path
    
    
    cortex = ctypes.CDLL(DLL_path)
    # Declare the return types of the functions
    cortex.start_camera.restype = ctypes.c_int
    cortex.get_width.restype = ctypes.c_int
    cortex.get_height.restype = ctypes.c_int
    cortex.get_frame.restype = ctypes.POINTER(ctypes.c_ubyte)
    cortex.stop_camera.restype = ctypes.c_int
    cortex.get_format.restype = ctypes.c_char_p
    cortex.get_stride.restype = ctypes.c_int
    cortex.get_frame_length.restype = ctypes.c_int

    # Start the camera
    result = cortex.start_camera()
    if result != 0:
        raise RuntimeError(f"{_ANSI.red()} [!]Failed to start camera. Error code: {result}{_ANSI.reset()}")

    format_ptr = cortex.get_format()
    format_str = format_ptr.decode('utf-8') if format_ptr else ""
    # print(f"Camera started. Format: {format_str}")

    try:
        while True:
            frame_ptr = cortex.get_frame()
            if not frame_ptr:
                continue

            if format_str == "MJPG":
                frame_length = cortex.get_frame_length()
                if frame_length > 0:
                    # Create a byte array from the pointer and the correct length
                    frame_bytes = np.ctypeslib.as_array((ctypes.c_ubyte * frame_length).from_address(ctypes.addressof(frame_ptr.contents)), shape=(frame_length,))
                    # Decode the JPEG frame
                    frame_array = cv2.imdecode(frame_bytes, cv2.IMREAD_COLOR)

                    if frame_array is not None:

                        # cv2.imshow("Live Feed", frame_array)
                        # Optionally get width and height here if needed later
                        # height, width, channels = frame_array.shape

                        yield frame_array.copy()
                    else:
                        print("Failed to decode MJPG frame")
                else:
                    print("Frame length is zero")

            elif format_str == "RGB32":
                width = cortex.get_width()
                height = cortex.get_height()
                frame_array = np.ctypeslib.as_array(frame_ptr, shape=(height, width, 4))
                bgr_frame = cv2.cvtColor(frame_array, cv2.COLOR_RGBA2BGR)

                # cv2.imshow("Live Feed", bgr_frame)
                yield frame_array.copy()

            elif format_str == "NV12":
                width = cortex.get_width()
                height = cortex.get_height()
                stride = cortex.get_stride()
                frame_size = int(height * (width * 1.5))
                frame_bytes = np.ctypeslib.as_array((ctypes.c_ubyte * frame_size).from_address(ctypes.addressof(frame_ptr.contents)), shape=(frame_size,))
                y_plane = frame_bytes[:height * width].reshape((height, width))
                uv_plane = frame_bytes[height * width:].reshape((height // 2, width))
                bgr_frame = cv2.cvtColor(np.concatenate(
                    (y_plane[:, :, np.newaxis],
                    cv2.resize(uv_plane, (width, height),
                    interpolation=cv2.INTER_LINEAR)[:, :, np.newaxis],
                    np.zeros((height, width, 1), dtype=np.uint8)), axis=2), cv2.COLOR_YUV2BGR_NV12)
                
                if bgr_frame is not None:
                    # cv2.imshow("Live Feed", bgr_frame)
                    yield frame_array.copy()
            else:
                print(f"{_ANSI.red()}[!] Unsupported format: {format_str}. Please don't hesitate to contact the developer to report this. {_ANSI.reset()}")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cortex.stop_camera()
        cv2.destroyAllWindows()

