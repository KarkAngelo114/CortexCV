import tkinter as tk
from PIL import *
from .._core import camera_viewer
from .._core.updateFrame import updateFrame
from .._core import visionInterpreter


def initiateView():
    vision = None
    bg = "black"

    try:
        view = tk.Tk()
        view.geometry("900x500")  # Initial window size
        view.title("CortexCV")
        view.configure(bg=bg)  # Optional: Set background color to black

        

        vision = camera_viewer.getCameraview()
        predicted = "Apple"
        score = 0.9889 * 100

        ctrl_panel = tk.Label(view, height=3, bg=bg, borderwidth=2, relief="solid")
        ctrl_panel.configure(highlightbackground="cyan", highlightcolor="cyan", highlightthickness=2)
        ctrl_panel.pack(side=tk.BOTTOM, fill=tk.X)  # Stick to the bottom and adjust width dynamically

        div1 = tk.Label(ctrl_panel, height=2, width=12, text=f"Predicted: {predicted}", fg="cyan", bg = bg)
        div1.pack(side=tk.LEFT)  # Stick to the left side of the parent
        div1.config(padx = 50)

        div2 = tk.Label(ctrl_panel, height=2, width=12, text=f"Accuracy: {score:.2f}%", fg="cyan", bg = bg)
        div2.pack(side=tk.RIGHT)  # Stick to the right side of the parent
        div2.config(padx = 50)
        
        # Create a label to display the camera feed
        mainPanel = tk.Label(view, bg="black")
        mainPanel.pack(fill=tk.BOTH, expand=True)  # Make it fill the entire window

        # Bind the <Configure> event to dynamically resize the camera view
        def resize(event):
            mainPanel.config(width=event.width, height=event.height)

        view.bind("<Configure>", resize)

        # Start updating the frame
        updateFrame(vision, mainPanel)

        # Bind the Escape key to close the window
        view.bind("<Escape>", lambda e: view.destroy())

        view.mainloop()
    finally:
        if vision and vision.isOpened():
            vision.release()