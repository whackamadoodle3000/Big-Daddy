#!/usr/bin/env python3
"""
Simple UI for Smart Student Monitor
Just a button to run the monitoring system
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os
import tkinter.messagebox as messagebox
from PIL import Image, ImageTk  # Import Pillow

# Import configuration
from config import OPENAI_API_KEY, validate_config

# Get the absolute path to the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


class SimpleStudentMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Big Daddy")
        self.root.geometry("800x450")
        self.root.configure(bg="white")
        
        # Keep a reference to the images to prevent garbage collection
        self.logo_image = None
        self.unlock_image = None

        # Center the window
        self.center_window()
        
        # Create the simple UI
        self.create_widgets()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_widgets(self):
        """Create the UI based on the image"""
        print("--- Starting to create widgets ---") # DEBUG
        
        # Try to use Fredoka font, fallback to system fonts
        try:
            # Test if Fredoka is available
            test_label = ttk.Label(self.root, text="Test", font=("Fredoka", 12))
            FONT_NAME = "Fredoka"
            print("Fredoka font is available")
        except:
            FONT_NAME = "Segoe UI"  # Fallback to Segoe UI on Windows
            print("Fredoka font not found, using Segoe UI")
        
        BLUE_COLOR = "#38B6FF"
        
        # Configure styles
        style = ttk.Style()
        style.configure("White.TFrame", background="white")
        style.configure("Blue.TLabel", background="white", foreground=BLUE_COLOR)
        style.configure("Blue.TButton", background=BLUE_COLOR, foreground="white", font=(FONT_NAME, 12, "bold"), borderwidth=0, relief="flat")
        style.map("Blue.TButton", background=[('active', '#5bc0ff')])

        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="5", style="White.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(2, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Left Side (Logo) ---
        logo_frame = ttk.Frame(main_frame, style="White.TFrame")
        logo_frame.grid(row=0, column=0, sticky="e", padx=5, pady=5)

        # Simple text instead of image for debugging
        # big_label = ttk.Label(logo_frame, text="BIG", font=(FONT_NAME, 120, "bold"), style="Blue.TLabel")
        # big_label.pack(expand=True, anchor="center")
        # daddy_label = ttk.Label(logo_frame, text="daddy 😊", font=(FONT_NAME, 50, "bold"), style="Blue.TLabel")
        # daddy_label.pack(expand=True, anchor="center")

        # Load logo image
        try:
            logo_path = os.path.join(ASSETS_DIR, "logo.png")
            print(f"Attempting to load logo icon from: {logo_path}") # DEBUG
            with Image.open(logo_path) as img:
                print("Logo image opened successfully with Pillow.") # DEBUG
                w, h = img.size
                # Make it much smaller - resize to 1/15 of original size
                img_resized = img.resize((w // 2, h // 2), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img_resized)
                print("Unlock ImageTk.PhotoImage created successfully.") # DEBUG
            logo_label = tk.Label(logo_frame, image=self.logo_image, bg="white", borderwidth=0)
            logo_label.image = self.logo_image  # Keep a reference!
            logo_label.pack(anchor="center")
        except (FileNotFoundError, IOError) as e:
            print(f"ERROR loading logo: {e}")
            # Fallback to text if image fails
            big_label = ttk.Label(logo_frame, text="BIG", font=(FONT_NAME, 120, "bold"), style="Blue.TLabel")
            big_label.pack(expand=True, anchor="center")
            daddy_label = ttk.Label(logo_frame, text="daddy 😊", font=(FONT_NAME, 50, "bold"), style="Blue.TLabel")
            daddy_label.pack(expand=True, anchor="center")

        # Unlock Button - now in column 0
        unlock_frame = ttk.Frame(main_frame, style="White.TFrame")
        unlock_frame.grid(row=0, column=1, pady=5, sticky="")
        
        try:
            unlock_path = os.path.join(ASSETS_DIR, "unlock.png")
            print(f"Attempting to load unlock icon from: {unlock_path}") # DEBUG
            with Image.open(unlock_path) as img:
                print("Unlock image opened successfully with Pillow.") # DEBUG
                w, h = img.size
                img_resized = img.resize((w // 3, h // 3), Image.Resampling.LANCZOS)
                self.unlock_image = ImageTk.PhotoImage(img_resized)
                print("Unlock ImageTk.PhotoImage created successfully.") # DEBUG

            unlock_button = tk.Button(unlock_frame, image=self.unlock_image, command=self.start_monitoring, borderwidth=0, bg="white", activebackground="white", cursor="hand2")
            unlock_button.image = self.unlock_image # Keep a reference!
            unlock_button.pack(pady=5)
            print("Unlock button created and packed.") # DEBUG
        except (FileNotFoundError, IOError) as e:
            print(f"ERROR loading unlock icon: {e}") # DEBUG
            unlock_button = ttk.Button(unlock_frame, text="unlock 🔒", command=self.start_monitoring, style="Blue.TButton", takefocus=False)
            unlock_button.pack(pady=5)

        
        # Timer Display - now in column 1
        timer_canvas = tk.Canvas(main_frame, bg="white", highlightthickness=0, width=250, height=200)
        timer_canvas.grid(row=0, column=2, pady=5, sticky="w")
        
        # Create rounded rectangle with taller height using arcs and lines
        radius = 15
        x1, y1, x2, y2 = 5, 5, 245, 195
        
        # Draw the rounded rectangle
        timer_canvas.create_arc(x1, y1, x1 + 2*radius, y1 + 2*radius, start=90, extent=90, outline=BLUE_COLOR, width=3, fill="white")
        timer_canvas.create_arc(x2 - 2*radius, y1, x2, y1 + 2*radius, start=0, extent=90, outline=BLUE_COLOR, width=3, fill="white")
        timer_canvas.create_arc(x1, y2 - 2*radius, x1 + 2*radius, y2, start=180, extent=90, outline=BLUE_COLOR, width=3, fill="white")
        timer_canvas.create_arc(x2 - 2*radius, y2 - 2*radius, x2, y2, start=270, extent=90, outline=BLUE_COLOR, width=3, fill="white")
        
        # Draw the straight lines
        timer_canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=BLUE_COLOR, width=3)
        timer_canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=BLUE_COLOR, width=3)
        timer_canvas.create_line(x1, y1 + radius, x1, y2 - radius, fill=BLUE_COLOR, width=3)
        timer_canvas.create_line(x2, y1 + radius, x2, y2 - radius, fill=BLUE_COLOR, width=3)

        timer_mins_label = ttk.Label(timer_canvas, text="37", font=(FONT_NAME, 50, "bold"), style="Blue.TLabel")
        timer_mins_label.place(relx=0.5, rely=0.3, anchor="center")

        timer_text_label = ttk.Label(timer_canvas, text="mins", font=(FONT_NAME, 30, "bold"), style="Blue.TLabel")
        timer_text_label.place(relx=0.5, rely=0.6, anchor="center")

        timer_break_label = ttk.Label(timer_canvas, text="since last break", font=(FONT_NAME, 15), style="Blue.TLabel")
        timer_break_label.place(relx=0.5, rely=0.85, anchor="center")
        
    def start_monitoring(self):
        """Start both the student monitoring system and emotion detection"""
        if not validate_config():
            messagebox.showerror("Error", "OpenAI API key not set!\nPlease run setup_env.py or create a .env file.")
            return
            
        try:
            # Build commands to run both scripts
            student_monitor_cmd = [sys.executable, "student_monitor.py"]
            emotion_detector_path = os.path.join(BASE_DIR, "emotion_detection", "debug_emotion_detector.py")
            emotion_detector_cmd = [sys.executable, emotion_detector_path]
            
            # Run both in new console windows (Windows)
            if sys.platform == "win32":
                # Start student monitor
                subprocess.Popen(["cmd", "/c", "start", "cmd", "/k"] + student_monitor_cmd, 
                               shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                
                # Start emotion detector
                subprocess.Popen(["cmd", "/c", "start", "cmd", "/k"] + emotion_detector_cmd, 
                               shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # For non-Windows systems
                subprocess.Popen(student_monitor_cmd)
                subprocess.Popen(emotion_detector_cmd)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring systems:\n{e}")


def main():
    """Main function"""
    root = tk.Tk()
    app = SimpleStudentMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 