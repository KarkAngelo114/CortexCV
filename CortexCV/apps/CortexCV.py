import tkinter as tk
import types
from PIL import Image, ImageTk
from .._utils import camera_viewer, _ANSI, usageReader
from .._core import visionInterpreter
import cv2
import threading
import queue
import time

def startCortexCV(threshold, input_shape, labels=[], models=[], callback_receiver = None, enable_GUI = False, debugLog = False):

    """
        The entry point of the CortexCV application.

        Parameters:
            threshold (float): specify the acceptable confidence score based on your needs

            input_shape (tuple): the input shape used in resizing the image during training of your models. Ex: (224, 224)

            labels (list): load your txt files that contains the classes when training your model. Be sure that they are not altered in any way.

            models (list): load your trained models to use them all at once during inference prediction

            callback_receiver (str): specify the defined function in your main file to receive the outputs during inference prediction in a form of callbacks.
                - ex: in your main.py you have this defined function:
                
.. code-block:: python
                from CortexCV.apps import CortexCV as cv

                def myFunction(prediction, score):
                    # your operations on what you will do to these outputs.
                    pass
                                    
                cv.startCortexCV(
                    . . . other parameters . . .
                    callback_receiver=myFunction,
                    . . . other parameters . . .
                )
            
            enable_GUI (bool): setting this to True will show a Live camera feed of what your camera sees, including the predicted output and the confidence score during inference

            debugLog (bool): set True to see the raw outputs in predicting

        Returns:
            a callback (prediction and score)
        Note:
            while you can load multiple models at once, be aware of the trade offs, especially when you're using live camera feed UI. Ex: frame drops, poor performance, and lags as your doing inference predictions which is already computational intensive, unless you have neough resources.

            loaded models must match the corresponding txt files in listing them in the list.
                ex:

                    labels = [labels1, labels2, labels3]
                    models = [model1, model2, model3]    
    """

    vision = None
    bg = "black"
    frame_queue = queue.Queue(maxsize=1)
    results_queue = queue.Queue()  # Queue for inference results
    usage_queue = queue.Queue() # CPU/RAM usage

    def background_feed():
        while True:
            try:
                frame_source = vision
                frame = None
                if isinstance(frame_source, types.GeneratorType):
                    frame = next(frame_source)
                elif hasattr(frame_source, 'read'):
                    ret, frame = frame_source.read()
                    if not ret:
                        continue

                    panel_width = mainPanel.winfo_width()
                    panel_height = mainPanel.winfo_height()
                    if panel_width > 0 and panel_height > 0 and frame is not None:
                        frame = cv2.resize(frame, (panel_width, panel_height))

                if frame is not None:
                    try:
                        frame_queue.put(frame.copy(), block=False)
                    except queue.Full:
                        pass
            except StopIteration:
                break
            except Exception as e:
                print(f"[Background Camera Error] {e}")

    def inference_thread():
        while True:
            try:
                frame = frame_queue.get()  # Blocking get
                small_frame = cv2.resize(frame, (input_shape[1], input_shape[0]))
                predicted, score = visionInterpreter.cortexOperation(threshold, small_frame, input_shape, models, labels, debugLog)
                results_queue.put((predicted, score))
                if callback_receiver:
                    callback_receiver(predicted, score)  # Call callback
            except Exception as e:
                print(f"{_ANSI.red()}[Inference Error] {e}{_ANSI.reset()}", end ="\r")

    

    vision = camera_viewer.getCameraview()
    # Start camera thread
    threading.Thread(target=background_feed, daemon=True).start()

    # Start inference thread
    threading.Thread(target=inference_thread, daemon=True).start()

    if enable_GUI:
        view = tk.Tk()
        view.geometry("900x500")
        view.title("CortexCV")
        view.configure(bg=bg)

        topLabelWidget = tk.Label(view, height = 2, bg = bg, borderwidth=1, relief="solid")
        topLabelWidget.configure(highlightbackground="cyan", highlightcolor="cyan", highlightthickness = 2)
        topLabelWidget.pack(side=tk.TOP, fill=tk.X)

        CPUlabel = tk.Label(topLabelWidget, height=2, width=12, bg = bg, fg = "cyan")
        CPUlabel.pack(side="left")

        RAMlabel = tk.Label(topLabelWidget, height=2, width=12, bg = bg, fg = "cyan")
        RAMlabel.pack(side="left")
        

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
        view.bind("<Escape>", lambda e: view.destroy())

        def getUsage():
            try:
                while True:
                    CPU, RAM = usageReader.getUsage()
                    usage_queue.put((CPU, RAM))
            except Exception as e:
                print(f"{_ANSI.red()}{e}{_ANSI.reset()}")

        def readUsage():
            try:
                CPU, RAM = usage_queue.get(block=False)
                CPUlabel.config(text=f"CPU: {CPU}%")
                RAMlabel.config(text=f"RAM: {RAM}%")
                
            except queue.Empty:
                pass
            view.after(1, readUsage)


        def update_gui():
            try:
                frame = frame_queue.get(block=False)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame.shape[2] == 3 else frame
                img = ImageTk.PhotoImage(Image.fromarray(rgb))
                mainPanel.config(image=img)
                mainPanel.image = img

                try:
                    predicted, score = results_queue.get(block=False)
                    div1.config(text=f"Predicted: {predicted}")
                    div2.config(text=f"Confidence Score: {score:.2f}%")
                except queue.Empty:
                    pass
            except queue.Empty:
                pass
            except Exception as e:
                print(f"[GUI Error] {e}")
            view.after(1, update_gui)

        threading.Thread(target=getUsage, daemon=True).start()
        update_gui()
        readUsage()
        view.mainloop()
        

    if vision and hasattr(vision, 'release'):
        vision.release()

    if not enable_GUI:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{_ANSI.yellow()}>> CortexCV gracefully shutting down... {_ANSI.reset()}")


    