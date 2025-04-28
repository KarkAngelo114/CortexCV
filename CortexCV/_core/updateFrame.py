from PIL import Image, ImageTk
import cv2

def updateFrame(cap, panel):
    def update():
        ret, frame = cap.read()
        if ret:
            # Resize the frame to match the panel size
            panel_width = panel.winfo_width()
            panel_height = panel.winfo_height()
            if panel_width > 0 and panel_height > 0:
                frame = cv2.resize(frame, (panel_width, panel_height))

            # Convert from BGR (OpenCV) to RGB (PIL)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            panel.imgtk = imgtk  # Store a reference to prevent garbage collection
            panel.config(image=imgtk)

        # Repeat after 10 milliseconds
        panel.after(10, update)

    update()

        
