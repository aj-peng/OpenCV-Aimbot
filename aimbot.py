
import winsound
import win32api
import win32con
from tkinter import *
import numpy as np
import mss
import cv2

def is_aiming():
    return win32api.GetAsyncKeyState(0x02) < 0

def load_template(file_path):
    # Load and convert template image to grayscale
    template = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
    if template is None:
        print(f"Error: Could not load template from {file_path}")
        return None

    return cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

def perform_aim_action(offset_x, offset_y):
    # print(f'AIMING: {offset_x}, {offset_y}')
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, offset_x, offset_y, 0, 0)

class Config:
    def __init__(self):
        # Display resolution
        self.screen_width = 1920
        self.screen_height = 1200
        self.capture_size = 128

        self.screen_center_x = self.screen_width // 2
        self.screen_center_y = self.screen_height // 2
        self.capture_radius = self.capture_size // 2

        self.compensation = 0.3 # (0 < value < 1)
        self.sensitivity_scalar = 0.55 # Based on game
        self.mouse_sensitivity = 0.36
        self.game_sensitivity = 0.45
        self.aim_sensitivity = 0.85
        self.sensitivity = self.calculate_sensitivity()

        self.template = load_template("indicator.png")
        self.template_height = self.template.shape[0]
        self.template_width = self.template.shape[1]
        self.template_center_y = self.template_height // 2
        self.template_center_x = self.template_width // 2

        # Capture region around crosshair
        self.regions = {
            "top": self.screen_center_y - self.capture_radius,
            "left": self.screen_center_x - self.capture_radius,
            "width": self.capture_size,
            "height": self.capture_size
        }

    def calculate_sensitivity(self):
        converted = self.mouse_sensitivity * self.aim_sensitivity
        return ((self.game_sensitivity * converted) / self.sensitivity_scalar) + self.compensation

class Controller:
    def __init__(self):
        self.config = Config()
        self.screen_capture = mss.mss()

        self.active = False
        self.running = False

        self.width = 480
        self.height = 240

        self.window = Tk()
        self.window.title("Aimbot")
        self.window.resizable(False, False)

        self.canvas = Canvas(self.window, bg="#000000", height=self.height, width=self.width)
        self.canvas.focus_set()
        self.canvas.pack()

        x,y = self.width // 2, self.height // 2 - 48
        self.canvas.create_text(x, y, text="Press UP to toggle ON/OFF", font=("Arial", 18), fill="white", tags="menu")
        self.canvas.create_text(x, y + 48, text="Press DOWN to exit", font=("Arial", 18), fill="white", tags="menu")
        self.status_text_id = self.canvas.create_text(x, y + 96, text="STATUS: OFF", font=("Arial", 18), fill="red", tags="status")

    def capture_game_frame(self):
        # Capture screen region around crosshair
        frame = np.array(self.screen_capture.grab(self.config.regions))
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

    def calculate_aim_offset(self, target_location):
        # Calculate mouse movement needed to aim at target
        target_x = target_location[0] + self.config.template_center_x
        target_y = target_location[1] + self.config.template_center_y

        offset_x = (-(self.config.capture_radius - target_x)) * self.config.sensitivity
        offset_y = (-(self.config.capture_radius - target_y)) * self.config.sensitivity

        return int(offset_x), int(offset_y)

    def find_target(self, game_frame):
        # Find target using template matching
        result = cv2.matchTemplate(game_frame, self.config.template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Confidence threshold (adjust as needed)
        if max_val >= 0.8:
            return max_loc, max_val
        return None, max_val

    def toggle(self):
            self.active = not self.active
            if self.active:
                winsound.Beep(1000, 100)
                self.canvas.itemconfig(self.status_text_id, text="STATUS: ON", fill="green")
            else:
                winsound.Beep(500, 100)
                self.canvas.itemconfig(self.status_text_id, text="STATUS: OFF", fill="red")

    def run(self, *args):
        if not self.window.winfo_exists():
            return

        if self.active and is_aiming():
            game_frame = self.capture_game_frame()
            target_location, confidence = self.find_target(game_frame)
            if target_location:
                offset_x, offset_y = self.calculate_aim_offset(target_location)
                perform_aim_action(offset_x, offset_y)
                # winsound.Beep(1250, 100)

        if self.window.winfo_exists():
            self.window.after(1, self.run, ())

    def exit(self):
        self.active = False
        self.window.destroy()

    def start(self):
        self.window.protocol("WM_DELETE_WINDOW", self.exit)
        self.window.bind('<Up>', lambda event: self.toggle())
        self.window.bind('<Down>', lambda event: self.exit())

        self.run()
        self.window.mainloop()

if __name__ == "__main__":
    try:
        aimbot = Controller()
        aimbot.start()
    except KeyboardInterrupt:
        pass