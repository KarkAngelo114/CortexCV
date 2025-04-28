import tkinter as tk
from PIL import *
from .._utils import camera_viewer
from .._utils.updateFrame import updateFrame
from .._core import visionInterpreter
import cv2  # Important for resizing frames

def initiateView(input_shape, labels=[], models=[]):
    vision = None
    bg = "black"

    def predict_and_update():
        # Grab a frame safely
        ret, frame = vision.read()
        if ret:
            # Resize the frame to model input size for faster processing
            small_frame = cv2.resize(frame, (input_shape[1], input_shape[0]))

            # Predict on the resized frame
            predicted, score = visionInterpreter.cortexOperation(small_frame, input_shape, models, labels)

            # Update GUI text
            div1.config(text=f"Predicted: {predicted}")
            div2.config(text=f"Accuracy: {score:.2f}%")

        # Predict again after 200ms (5 times per second) - smoother
        view.after(2500, predict_and_update)

    try:
        view = tk.Tk()
        view.geometry("900x500")
        view.title("CortexCV")
        view.configure(bg=bg)

        vision = camera_viewer.getCameraview()

        ctrl_panel = tk.Label(view, height=3, bg=bg, borderwidth=2, relief="solid")
        ctrl_panel.configure(highlightbackground="cyan", highlightcolor="cyan", highlightthickness=2)
        ctrl_panel.pack(side=tk.BOTTOM, fill=tk.X)

        div1 = tk.Label(ctrl_panel, height=2, width=12, text="Predicted: ", fg="cyan", bg=bg)
        div1.pack(side=tk.LEFT)
        div1.config(padx=50)

        div2 = tk.Label(ctrl_panel, height=2, width=12, text="Confidence Score: ", fg="cyan", bg=bg)
        div2.pack(side=tk.RIGHT)
        div2.config(padx=50)

        mainPanel = tk.Label(view, bg="black")
        mainPanel.pack(fill=tk.BOTH, expand=True)

        def resize(event):
            mainPanel.config(width=event.width, height=event.height)

        view.bind("<Configure>", resize)
        updateFrame(vision, mainPanel)
        view.bind("<Escape>", lambda e: view.destroy())

        # Start predicting
        predict_and_update()

        # Start the GUI
        view.mainloop()

    finally:
        if vision and vision.isOpened():
            vision.release()
