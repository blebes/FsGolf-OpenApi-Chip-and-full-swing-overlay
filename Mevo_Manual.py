import tkinter as tk
import pyautogui
# We import pygetwindow securely inside the functions now to prevent startup crashes
import time
import os
import json
import sys

# Catch-all for missing libraries in the exe
try:
    import pygetwindow as gw
except ImportError:
    # This usually shouldn't happen if pyinstaller worked, but good safety
    pass

pyautogui.FAILSAFE = False

# ================= CONFIG =================
COORD_FILE = "coords_manual.json"

DEFAULT_DATA = {
    "chip_click": (1683, 40),
    "full_click": (1511, 40)
}

# Load Config Safely
if os.path.exists(COORD_FILE):
    try:
        with open(COORD_FILE, "r") as f:
            APP_DATA = json.load(f)
    except:
        APP_DATA = DEFAULT_DATA
else:
    APP_DATA = DEFAULT_DATA

# Colors
ACTIVE_COLORS = {"chip": "#4CAF50", "full": "#388E3C"}
INACTIVE_BG = "#2E2E2E"
FG = "white"
FONT = ("Arial", 12, "bold")

BTN_WIDTH_PX = 130
BTN_HEIGHT_PX = 50

# ================= HELPERS =================
def safe_activate(win):
    try:
        if win.isMinimized:
            win.restore()
            time.sleep(0.2)
        win.activate()
    except Exception as e:
        print(f"Window activation error: {e}")

def save_app_data():
    try:
        with open(COORD_FILE, "w") as f:
            json.dump(APP_DATA, f)
    except Exception as e:
        status_var.set("Error saving settings")

# ================= BUTTON CLASS =================
class OvalButton(tk.Canvas):
    def __init__(self, master, text, command, right_command, bg, fg, width, height):
        super().__init__(master, width=width, height=height, bg="black", highlightthickness=0)
        self.command = command
        self.right_command = right_command
        
        self.oval = self.create_oval(2, 2, width-2, height-2, fill=bg, outline=bg)
        self.text = self.create_text(width/2, height/2, text=text, fill=fg, font=FONT)
        
        self.bind("<Button-1>", self.on_click)
        self.tag_bind(self.oval, "<Button-1>", self.on_click)
        self.tag_bind(self.text, "<Button-1>", self.on_click)

        self.bind("<Button-3>", self.on_right_click)
        self.tag_bind(self.oval, "<Button-3>", self.on_right_click)
        self.tag_bind(self.text, "<Button-3>", self.on_right_click)

    def on_click(self, event):
        if self.command: self.command()

    def on_right_click(self, event):
        if self.right_command: self.right_command()

    def config(self, **kwargs):
        if 'bg' in kwargs:
            self.itemconfig(self.oval, fill=kwargs['bg'], outline=kwargs['bg'])
        if 'fg' in kwargs:
            self.itemconfig(self.text, fill=kwargs['fg'])

# ================= LOGIC =================
def set_active_ui(mode):
    chip_btn.config(bg=INACTIVE_BG)
    full_btn.config(bg=INACTIVE_BG)

    if mode == "chip":
        chip_btn.config(bg=ACTIVE_COLORS["chip"])
        status_var.set("MODE: Chip")
    elif mode == "full":
        full_btn.config(bg=ACTIVE_COLORS["full"])
        status_var.set("MODE: Full")

def switch_fs_mode(mode):
    global current_mode
    if current_mode == mode:
        return

    try:
        # Check if windows exist only when we click, not at startup
        fs_list = gw.getWindowsWithTitle("FS Golf")
        gs_list = gw.getWindowsWithTitle("GSPro")
        
        if not fs_list:
            status_var.set("ERR: FS Golf Not Open")
            return
        
        # 1. Activate FS Golf
        fs = fs_list[0]
        safe_activate(fs)
        time.sleep(0.2)

        # 2. Click the button
        key = f"{mode}_click"
        if key in APP_DATA:
            x, y = APP_DATA[key]
            pyautogui.click(x, y)
        
        # 3. Return to GSPro (if open)
        if gs_list:
            safe_activate(gs_list[0])
        else:
            status_var.set("Warning: GSPro Not Open")

        current_mode = mode
        set_active_ui(mode)
        
    except Exception as e:
        status_var.set("Error: " + str(e))
        print("Error:", e)

def calibrate_click_coord(mode):
    try:
        for i in range(5, 0, -1):
            status_var.set(f"Hover {mode.upper()} btn: {i}s")
            root.update()
            time.sleep(1)
        
        x, y = pyautogui.position()
        APP_DATA[f"{mode}_click"] = (x, y)
        save_app_data()
        status_var.set(f"Saved {mode}: {x},{y}")
        root.after(1000, lambda: set_active_ui(current_mode))
    except Exception as e:
        status_var.set("Calibrate Error")

# ================= UI SETUP =================
# We wrap the main execution in a try/except so if it fails, we see why
try:
    root = tk.Tk()
    root.title("Mevo Switcher")
    root.attributes("-topmost", True)
    root.geometry("400x150")
    root.configure(bg="black")

    status_var = tk.StringVar()
    status_var.set("Right-Click btns to calibrate")
    status_label = tk.Label(root, textvariable=status_var, font=("Arial", 12, "bold"), fg="yellow", bg="black")
    status_label.pack(pady=10)

    button_frame = tk.Frame(root, bg="black")
    button_frame.pack(pady=5)

    chip_btn = OvalButton(button_frame, text="Chip", fg=FG, bg=INACTIVE_BG, width=BTN_WIDTH_PX, height=BTN_HEIGHT_PX,
        command=lambda: switch_fs_mode("chip"),
        right_command=lambda: calibrate_click_coord("chip")
    )
    chip_btn.pack(side="left", padx=15)

    full_btn = OvalButton(button_frame, text="Full", fg=FG, bg=INACTIVE_BG, width=BTN_WIDTH_PX, height=BTN_HEIGHT_PX,
        command=lambda: switch_fs_mode("full"),
        right_command=lambda: calibrate_click_coord("full")
    )
    full_btn.pack(side="left", padx=15)

    current_mode = "unknown"
    set_active_ui("full") 

    root.mainloop()

except Exception as e:
    # If a critical error happens at startup, this keeps the window open
    # so you can actually read what went wrong.
    print("CRITICAL CRASH:", e)
    input("Press Enter to close...")