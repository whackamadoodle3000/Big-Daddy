import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
from deepface import DeepFace
import os
from datetime import datetime
from collections import defaultdict, deque

class DebugEmotionDetector:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        
        self.cap = None
        self.is_running = False
        self.current_emotion = "No face detected"
        self.emotion_confidence = 0.0
        self.debug_info = "Initializing..."
        
        # Emotion tracking with sliding window
        self.emotion_window = deque(maxlen=30)  # 3 seconds * 10 FPS = 30 frames
        self.window_duration = 3.0  # 3 seconds
        
        # New emotion recording system
        self.counter = 0  # Counter that starts at 0
        self.emotionCache = [[0.0] * 7 for _ in range(20)]  # 2D array with 20 entries, each entry is size 7
        self.emotionScore = [0.0] * 7  # Array with size 7, each entry corresponds to an emotion
        self.last_record_time = time.time()
        
        # Emotion labels
        self.emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        
        # Create GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the main GUI window with debug information"""
        self.root = tk.Tk()
        self.root.title("Debug Emotion Detection System")
        self.root.geometry("900x700")
        self.root.configure(bg='#2c3e50')
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='white')
        style.configure('Emotion.TLabel', font=('Arial', 14), foreground='#ecf0f1')
        style.configure('Confidence.TLabel', font=('Arial', 12), foreground='#bdc3c7')
        style.configure('Debug.TLabel', font=('Arial', 10), foreground='#e74c3c')
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="Debug Emotion Detection", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Video frame
        self.video_frame = tk.Frame(main_frame, bg='#34495e', relief='raised', bd=2)
        self.video_frame.pack(pady=10)
        
        self.video_label = tk.Label(self.video_frame, bg='#34495e')
        self.video_label.pack(padx=10, pady=10)
        
        # Debug information frame
        debug_frame = tk.Frame(main_frame, bg='#2c3e50')
        debug_frame.pack(pady=10, fill='x')
        
        # Debug info label
        self.debug_label = ttk.Label(debug_frame, text="Debug: Initializing...", 
                                    style='Debug.TLabel', wraplength=800)
        self.debug_label.pack()
        
        # Emotion display frame
        emotion_frame = tk.Frame(main_frame, bg='#2c3e50')
        emotion_frame.pack(pady=10)
        
        # Current emotion
        self.emotion_label = ttk.Label(emotion_frame, text="Emotion: No face detected", 
                                      style='Emotion.TLabel')
        self.emotion_label.pack()
        
        # Confidence
        self.confidence_label = ttk.Label(emotion_frame, text="Confidence: 0%", 
                                         style='Confidence.TLabel')
        self.confidence_label.pack()
        
        # Window info display
        self.window_label = ttk.Label(emotion_frame, text="Window: 0/3.0s", 
                                     style='Confidence.TLabel')
        self.window_label.pack()
        
        # Counter display
        self.counter_label = ttk.Label(emotion_frame, text="Counter: 0/20", 
                                      style='Confidence.TLabel')
        self.counter_label.pack()
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg='#2c3e50')
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(button_frame, text="Start Camera", 
                                     command=self.start_camera,
                                     bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                     relief='flat', padx=20, pady=10)
        self.start_button.pack(side='left', padx=10)
        
        self.stop_button = tk.Button(button_frame, text="Stop Camera", 
                                    command=self.stop_camera,
                                    bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                                    relief='flat', padx=20, pady=10, state='disabled')
        self.stop_button.pack(side='left', padx=10)
        
        # Status bar
        self.status_label = tk.Label(main_frame, text="Ready to start", 
                                    bg='#34495e', fg='white', font=('Arial', 10))
        self.status_label.pack(pady=10)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def start_camera(self):
        """Start the webcam and emotion detection"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Could not open webcam")
            
            self.is_running = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.status_label.config(text="Camera started - Detecting emotions...")
            
            # Start video processing in a separate thread
            self.video_thread = threading.Thread(target=self.process_video)
            self.video_thread.daemon = True
            self.video_thread.start()
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            
    def stop_camera(self):
        """Stop the webcam and emotion detection"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Camera stopped")
        
        # Clear video display
        self.video_label.config(image='')
        
    def calculate_emotion_score(self):
        """Calculate emotionScore based on weighted history"""
        # Set all values in emotionScore to 0
        self.emotionScore = [0.0] * 7
        
        # Loop through the emotionCache
        for i in range(20):
            # Calculate time difference: (counter - current index of emotionCache)
            time_diff = (self.counter - i) % 20  # Handle wraparound
            
            # Determine weight based on time difference
            if time_diff <= 5:
                weight = 100 - 10 * time_diff
            elif time_diff <= 10:
                weight = 75 - 5 * time_diff
            else:
                weight = 25
                
            # Add weighted values to emotionScore for each emotion
            for emotion_idx in range(7):
                self.emotionScore[emotion_idx] += self.emotionCache[i][emotion_idx] * weight
                
    def record_emotion_data(self):
        """Record emotion data every 3 seconds"""
        current_time = time.time()
        
        # Check if 3 seconds have passed
        if current_time - self.last_record_time >= 3.0:
            # Calculate emotion presence times for ALL emotions in the current window
            emotion_counts = defaultdict(int)
            total_frames = len(self.emotion_window)
            
            if total_frames > 0:
                for emotion, timestamp in self.emotion_window:
                    emotion_counts[emotion] += 1
                
                # Calculate presence time for ALL emotions and record in emotionCache
                for i, emotion in enumerate(self.emotions):
                    count = emotion_counts.get(emotion, 0)
                    presence_time = (count / total_frames) * self.window_duration
                    self.emotionCache[self.counter][i] = presence_time
                
                # Calculate emotionScore
                self.calculate_emotion_score()
                
                # Log to emotionLog.txt
                self.log_emotion_scores()
                
                # Log the recording
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n{'='*60}")
                print(f"RECORDING EMOTION DATA - Counter: {self.counter}/20")
                print(f"Time: {timestamp}")
                print("Emotion presence times in current 3s window:")
                for i, emotion in enumerate(self.emotions):
                    presence_time = self.emotionCache[self.counter][i]
                    print(f"  {emotion}: {presence_time:.1f}s")
                print("\nCurrent emotionScores:")
                for i, emotion in enumerate(self.emotions):
                    score = self.emotionScore[i]
                    print(f"  {emotion}: {score:.1f}")
                print(f"{'='*60}\n")
                
                # Increment counter
                self.counter += 1
                if self.counter >= 20:
                    self.counter = 0
                
                # Update last record time
                self.last_record_time = current_time
                
    def log_emotion_scores(self):
        """Log emotion scores to emotionLog.txt"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create compact log entry
        log_entry = f"{timestamp}"
        for i, emotion in enumerate(self.emotions):
            score = self.emotionScore[i]
            log_entry += f" {emotion}:{score:.1f}"
        log_entry += "\n"
        
        # Write to file
        try:
            with open("emotionLog.txt", "a") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to emotionLog.txt: {e}")
        
    def update_emotion_window(self, emotion):
        """Add current emotion to the sliding window"""
        current_time = time.time()
        self.emotion_window.append((emotion, current_time))
        
    def get_window_stats(self):
        """Get current window statistics for display"""
        if len(self.emotion_window) == 0:
            return "Window: 0/3.0s", {}
            
        emotion_counts = defaultdict(int)
        for emotion, timestamp in self.emotion_window:
            emotion_counts[emotion] += 1
            
        total_frames = len(self.emotion_window)
        window_time = total_frames * 0.1  # 10 FPS = 0.1 seconds per frame
        
        # Find most common emotion
        if emotion_counts:
            most_common = max(emotion_counts.items(), key=lambda x: x[1])
            emotion, count = most_common
            presence_time = (count / total_frames) * window_time
            window_text = f"Window: {presence_time:.1f}/{window_time:.1f}s ({emotion})"
        else:
            window_text = f"Window: 0.0/{window_time:.1f}s"
            
        return window_text, dict(emotion_counts)
        
    def process_video(self):
        """Process video frames and detect emotions with debug info"""
        frame_count = 0
        emotion_detection_count = 0
        
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                self.debug_info = "Failed to read frame from camera"
                self.root.after(0, self.update_debug_display)
                continue
                
            frame_count += 1
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            results = self.face_detection.process(rgb_frame)
            
            if results.detections:
                self.debug_info = f"Face detected! Frame: {frame_count}"
                
                for detection in results.detections:
                    # Draw face detection box
                    bboxC = detection.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    bbox = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                           int(bboxC.width * iw), int(bboxC.height * ih)
                    
                    cv2.rectangle(frame, bbox, (0, 255, 0), 2)
                    
                    # Extract face region for emotion detection
                    face_region = frame[bbox[1]:bbox[1]+bbox[3], bbox[0]:bbox[0]+bbox[2]]
                    
                    if face_region.size > 0:
                        self.debug_info = f"Face region extracted: {face_region.shape}"
                        
                        # Detect emotion using DeepFace
                        try:
                            self.debug_info = "Starting DeepFace analysis..."
                            self.root.after(0, self.update_debug_display)
                            
                            emotion_result = DeepFace.analyze(face_region, 
                                                           actions=['emotion'], 
                                                           enforce_detection=False)
                            
                            if isinstance(emotion_result, list):
                                emotion_result = emotion_result[0]
                            
                            emotion = emotion_result['dominant_emotion']
                            confidence = max(emotion_result['emotion'].values())
                            
                            self.current_emotion = emotion.capitalize()
                            self.emotion_confidence = confidence
                            emotion_detection_count += 1
                            
                            # Update emotion window
                            self.update_emotion_window(emotion)
                            
                            # Record emotion data every 3 seconds
                            self.record_emotion_data()
                            
                            # Get window statistics
                            window_text, emotion_stats = self.get_window_stats()
                            
                            self.debug_info = f"Emotion: {emotion} ({confidence:.1%}) - Detection #{emotion_detection_count} - {window_text}"
                            
                            # Update GUI labels
                            self.root.after(0, lambda: self.update_emotion_display(window_text))
                            
                        except Exception as e:
                            self.debug_info = f"DeepFace error: {str(e)}"
                            self.current_emotion = "Detection failed"
                            self.emotion_confidence = 0.0
                            self.update_emotion_window("Detection failed")
                            self.record_emotion_data()
                            window_text, _ = self.get_window_stats()
                            self.root.after(0, lambda: self.update_emotion_display(window_text))
                    else:
                        self.debug_info = "Face region is empty or too small"
                        self.current_emotion = "Face too small"
                        self.emotion_confidence = 0.0
                        self.update_emotion_window("Face too small")
                        self.record_emotion_data()
                        window_text, _ = self.get_window_stats()
                        self.root.after(0, lambda: self.update_emotion_display(window_text))
            else:
                self.current_emotion = "No face detected"
                self.emotion_confidence = 0.0
                self.update_emotion_window("No face detected")
                self.record_emotion_data()
                window_text, _ = self.get_window_stats()
                self.debug_info = f"No face detected in frame {frame_count}"
                self.root.after(0, lambda: self.update_emotion_display(window_text))
            
            # Update debug display
            self.root.after(0, self.update_debug_display)
            
            # Convert frame for GUI display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            
            # Resize frame to fit GUI
            display_width = 640
            display_height = 480
            frame_pil = frame_pil.resize((display_width, display_height), Image.Resampling.LANCZOS)
            
            frame_tk = ImageTk.PhotoImage(frame_pil)
            
            # Update video display
            self.root.after(0, lambda: self.video_label.config(image=frame_tk))
            self.root.after(0, lambda: setattr(self.video_label, 'image', frame_tk))
            
            # Control frame rate
            time.sleep(0.1)  # ~10 FPS for better window analysis
            
    def update_emotion_display(self, window_text):
        """Update emotion and confidence labels in GUI"""
        self.emotion_label.config(text=f"Emotion: {self.current_emotion}")
        self.confidence_label.config(text=f"Confidence: {self.emotion_confidence:.1%}")
        self.window_label.config(text=window_text)
        self.counter_label.config(text=f"Counter: {self.counter}/20")
        
    def update_debug_display(self):
        """Update debug information in GUI"""
        self.debug_label.config(text=f"Debug: {self.debug_info}")
        
    def on_closing(self):
        """Handle window closing"""
        self.stop_camera()
        self.root.destroy()
        
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

def main():
    """Main function to run the debug emotion detector"""
    print("Starting Enhanced Emotion Detection System...")
    print("This version uses a 3-second sliding window approach.")
    print("Emotion data is recorded every 3 seconds in emotionCache.")
    print("EmotionScore is calculated with weighted history.")
    print()
    
    detector = DebugEmotionDetector()
    detector.run()

if __name__ == "__main__":
    main() 