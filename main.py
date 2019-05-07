import sys
import cv2 #
import os #
import numpy as np #
import pandas as pd #
import time #
import threading #
import argparse #
import csv #
import vlc

import tkinter as Tk
import pathlib
import time
import platform

from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter import Label
from collections import deque
from threading import Thread, Event
from PIL import Image
from PIL import ImageTk

RATE = 30
TIMESHOWN = 20
WINDOWLEN = RATE * TIMESHOWN
class ttkTimer(Thread):
    """a class serving same function as wxTimer... but there may be better ways to do this
    """

    def __init__(self, callback, tick):
        Thread.__init__(self)
        self.callback = callback
        self.stopFlag = Event()
        self.tick = tick
        self.iters = 0

    def run(self):
        while not self.stopFlag.wait(self.tick):
            self.iters += 1
            self.callback()

    def stop(self):
        self.stopFlag.set()

    def get(self):
        return self.iters


class Player(Tk.Frame):
    """The main window has to deal with events.
    """

    def __init__(self, parent, rating_meter, title=None, speed=1):
        Tk.Frame.__init__(self, parent)

        self.parent = parent
        self.parent.config(bg='black')
        self.parent.attributes('-fullscreen', True)

        if title == None:
            title = "tk_vlc"
        self.parent.title(title)

        self.rating_meter = rating_meter

        # The second panel holds controls
        self.player = None
        self.videopanel = Tk.Frame(self.parent)

        self.canvas = Tk.Canvas(self.videopanel, bg='black', highlightbackground='black').pack(fill=Tk.BOTH,
                                                      expand=1)
        self.videopanel.pack(fill=Tk.BOTH, expand=1)


        # convert the images to PIL format...

        # ...and then to ImageTk format
        image = ImageTk.PhotoImage(Image.fromarray(self.rating_meter.get_image_of_rating()[:, :, [2, 1, 0]]))

        self.panelA = Label(image=image)
        self.panelA.image = image
        self.panelA.pack(side="left", padx=10, pady=10)

        # Keybindings
        self.parent.bind("<Escape>", self.Escape)
        self.parent.bind("<Return>", self.start_running_rating_meter)
        self.parent.bind("<space>", self.key_press_listener)
        self.parent.bind("<KeyRelease-space>", self.key_release_listener)

        # VLC player controls
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()

        media = self.Instance.media_new(rating_meter.filename)
        self.player.set_media(media)
        self.player.audio_set_volume(100)
        self.player.play()

        self.player.set_rate(speed)  # rate of playback

        self.graphtimer = ttkTimer(self.OnGraphTimer, 1 / 120)
        self.graphtimer.start()

        self.parent.update()

        if platform.system() == 'Windows':
            self.player.set_hwnd(self.GetHandle())
        else:
            self.player.set_xwindow(self.GetHandle())  # this line messes up windows

        if not self.rating_meter.video_length:
            time.sleep(1)
            self.rating_meter.video_length = self.player.get_length()

    def GetHandle(self):
        return self.videopanel.winfo_id()

    def Escape(self, _):
        self.quit()
        if self.rating_meter.running:
            self.rating_meter.process_csv_file()
        self.destroy()
        os._exit(0)

    def OnGraphTimer(self):
        """Update graph.
        """
        if (not self.rating_meter.running) and self.player.is_playing():
            self.player.pause()
        if self.rating_meter.running and not self.player.is_playing():
            self.player.play()
        if self.rating_meter.running and self.player.get_state() == vlc.State.Ended:
            self.quit()
            self.rating_meter.process_csv_file()
            self.destroy()
            os._exit(0)

        # convert the images to PIL format...
        self.rating_meter.video_time = self.player.get_time()
        self.record_rating_to_csv()

        # ...and then to ImageTk format
        image = ImageTk.PhotoImage(Image.fromarray(self.rating_meter.get_image_of_rating()[:, :, [2, 1, 0]]))
        self.panelA.configure(image=image)
        self.panelA.image = image

    def start_running_rating_meter(self, _):
        if not self.rating_meter.running:
            self.rating_meter.n = 0
        self.rating_meter.running = True

    def key_press_listener(self, _):
        with self.rating_meter.rating_lock:
            self.rating_meter.rating = 1

    def key_release_listener(self, _):
        with self.rating_meter.rating_lock:
            self.rating_meter.rating = 0

    def record_rating_to_csv(self, _=None):
        with self.rating_meter.rating_lock:
            self.rating_meter.rating_deque.append(self.rating_meter.rating)
            if self.rating_meter.running:
                self.rating_meter.writer.writerow([self.player.get_time(),
                                                   self.rating_meter.rating])

        self.rating_meter.csvfile.flush()

class RatingMeter:
    def __init__(self, filename):
        self.rating = 0
        self.rating_deque = deque([0 for _ in range(WINDOWLEN)], maxlen=WINDOWLEN)
        self.rating_lock = threading.Lock()
        self.running = False
        self.n = 0
        self.video_time = 0
        self.video_length = 0
        self.filename = filename

        self.width = 1920
        self.height = 200

        self.out_frame = np.zeros((self.height, self.width, 3)).astype('u1') # reset plot

        self.outfile = self.filename[:-4] + '_rating_results.csv'

        pts = np.zeros((len(self.rating_deque) + 2, 1, 2), np.int32)
        pts[1:-1, 0, 0] = np.arange(len(self.rating_deque))
        pts[0, 0, 0] = 0
        pts[0, 0, 1] = 100
        pts[-1, 0, 0] = len(self.rating_deque)
        pts[-1, 0, 1] = 100
        self.pts = pts
        
        self.csvfile = open(self.outfile, 'w', newline='')
        self.writer = csv.writer(self.csvfile)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.csvfile.close()

    def process_csv_file(self):

        # Load csv file as dataframe and remove duplicate index.
        df = pd.read_csv(self.outfile)
        df.drop_duplicates(keep='last', inplace=True)
        df.index = df.iloc[:, 0]
        df.drop(df.columns[0], axis=1, inplace=True)

        # Copy data of csv file into new dataframe with all timestamps.
        new_df = pd.DataFrame(pd.Series(data=np.nan, index=np.arange(self.video_length)))
        new_df.iloc[df.index.values[df.iloc[:, 0].values == 1]] = 1
        new_df.iloc[df.index.values[df.iloc[:, 0].values == 0]] = 0
        new_df.iloc[0] = 0

        # Fill NaNs with previous value (fill-forward).
        new_df.fillna(method='ffill', inplace=True)

        # Overwrite old file with processed version.
        new_df.to_csv(self.outfile)

    def get_image_of_rating(self):
        pts = self.pts

        # Capture frame-by-frame
        pts[1:-1, 0, 1] = -100*np.array(self.rating_deque) + 100
        plot = np.zeros((200, self.width, 3)).astype('u1')  # reset plot
        plot[::20, 20 - self.n % 20:: 5, :] = 255  # moving gridlines
        plot[::5, 20 - self.n % 20:: 20, :] = 255  # moving gridlines
        plot[100, :, :] = 255  # x axis

        cv2.fillPoly(plot, [pts], (200, 0, 0))
        plot[:100, :, :] = plot[:100, :, [0, 2, 1]]
        cv2.circle(plot, (pts[-2, 0, 0], pts[-2, 0, 1]), 2, (255, 255, 255), -1)

        frame = plot
        # Display the resulting frame

        if not self.running:
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, "Paused", (self.width // 2, self.height // 2), font, 4, (255, 255, 255), 5, cv2.LINE_AA)
            cv2.putText(frame, "Press enter to start", (self.width // 2, self.height // 2 + 50), font, 2,
                        (255, 255, 255), 2, cv2.LINE_AA)

        else:
            font = cv2.FONT_HERSHEY_PLAIN
            remaining_time = int(self.video_length - self.video_time)//1000
            cv2.putText(frame, "Press 'ESC' to quit", (2*self.width//3-200, self.height//4), font, 2, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, "Time remaining: {} s".format(remaining_time), (2*self.width//3-200, 3*self.height//4), font, 2,
                        (255, 255, 255), 2, cv2.LINE_AA)

        self.n += 1
        self.out_frame = plot.copy()
        return self.out_frame

class SelectVideoAndSpeedGUI:
    def __init__(self, master):
        self.master = master
        master.title("Video rating tool")

        self.master.config(bg='red')
        self.master.resizable(False, False)
        self.speed = 1
        self.filepath = ""
        self.cwd = os.path.dirname(os.path.dirname(os.getcwd()))

        self.label = ttk.Label(root, text="Set playing speed:")
        self.label.pack()

        self.speedbox = ttk.Combobox(root, width=12, textvariable=Tk.StringVar())
        self.speedbox.pack()
        self.speedbox['values'] = (1, 2, 5, 10, 0.25, 0.5, 0.75)
        self.speedbox.current(0)
        self.speedbox.bind("<<ComboboxSelected>>", self.read_speedbox)

        self.select_button = ttk.Button(master, text="Select video", command=self.select_video)
        self.select_button.pack()

        self.start_button = ttk.Button(root, text="Start rating", command=self.close_gui, state=Tk.DISABLED)
        self.start_button.pack()

    def read_speedbox(self, _):
        self.speed = float(self.speedbox.get())
        self.enable_start_button_if_file_set()

    def select_video(self):
        self.filepath = askopenfilename(initialdir=self.cwd,
                                   title="Select a video to rate",
                                   filetypes=(("mp4 files", "*.mp4"), ("avi files", "*.avi*")))

        self.enable_start_button_if_file_set()

    def close_gui(self):
        self.label.destroy()
        self.speedbox.destroy()
        self.select_button.destroy()
        self.start_button.destroy()
        self.master.quit()


    def enable_start_button_if_file_set(self):
        if self.filepath != "":
            self.start_button.config(state="normal")

def Tk_get_root():
    if not hasattr(Tk_get_root, "root"):  # (1)
        Tk_get_root.root = Tk.Tk()  # initialization call is inside the function
    return Tk_get_root.root

def quit():
    root = Tk_get_root()
    root.quit()  # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
    # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    os._exit(1)

if __name__ == "__main__":
    # Create a Tk.App(), which handles the windowing system event loop
    root = Tk_get_root()
    root.protocol("WM_DELETE_WINDOW", quit)
    my_gui = SelectVideoAndSpeedGUI(root)
    root.mainloop()

    speed = my_gui.speed
    filepath = my_gui.filepath

    with RatingMeter(filepath) as rating_meter:
        Player(root, rating_meter, title="Video rating tool", speed=speed)
        root.mainloop()
