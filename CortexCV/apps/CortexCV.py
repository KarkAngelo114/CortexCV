import tkinter as tk
import types
from PIL import Image, ImageTk
from .._utils import camera_viewer, _ANSI
from .._core import visionInterpreter
import cv2
import threading
import queue
import time

def startCortexCV(threshold, input_shape, labels=[], models=[], callback_receiver = None, enable_GUI = False):
    vision = None
    bg = "black"
    frame_queue = queue.Queue(maxsize=1)
    results_queue = queue.Queue()  # Queue for inference results
    

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
                predicted, score = visionInterpreter.cortexOperation(threshold, small_frame, input_shape, models, labels)
                results_queue.put((predicted, score))
                if callback_receiver:
                    callback_receiver(predicted, score)  # Call callback
            except Exception as e:
                print(f"[Inference Error] {e}")

    

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

        update_gui()
        view.mainloop()

    if vision and hasattr(vision, 'release'):
        vision.release()
        print(f"\n{_ANSI.yellow()}>> CortexCV gracefully shutting down...{_ANSI.reset()}")

    if not enable_GUI:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{_ANSI.yellow()}>> CortexCV gracefully shutting down... {_ANSI.reset()}")


    