import cv2
import mediapipe as mp
import numpy as np
import threading
import time
from deepface import DeepFace
import os
from datetime import datetime
from collections import defaultdict, deque

# Get the absolute path to the main project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
        
        print("Emotion Detection System Initialized")
        print("Starting camera and emotion detection...")
        
        # Start the camera automatically
        self.start_camera()
        
    def start_camera(self):
        """Start the webcam and emotion detection"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Could not open webcam")
            
            self.is_running = True
            print("Camera started successfully - Detecting emotions...")
            
            # Start video processing in the main thread
            self.process_video()
            
        except Exception as e:
            print(f"Error starting camera: {str(e)}")
            
    def stop_camera(self):
        """Stop the webcam and emotion detection"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        print("Camera stopped")
        
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
        
        # Debug: Print time difference
        time_diff = current_time - self.last_record_time
        print(f"DEBUG: Time since last record: {time_diff:.1f}s (need 3.0s)")
        
        # Check if 3 seconds have passed
        if current_time - self.last_record_time >= 3.0:
            print(f"DEBUG: 3 seconds passed! Recording emotion data...")
            
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
                print(f"DEBUG: Calling log_emotion_scores...")
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
                print(f"DEBUG: Updated last_record_time to: {self.last_record_time}")
            else:
                print(f"DEBUG: No frames in emotion window, skipping recording")
        else:
            print(f"DEBUG: Not enough time passed yet ({time_diff:.1f}s < 3.0s)")
        
    def log_emotion_scores(self):
        """Log emotion scores to emotionLog.txt"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create compact log entry
        log_entry = f"{timestamp}"
        for i, emotion in enumerate(self.emotions):
            score = self.emotionScore[i]
            log_entry += f" {emotion}:{score:.1f}"
        log_entry += "\n"
        
        # Get the full path for debugging
        log_file_path = os.path.join(BASE_DIR, "emotionLog.txt")
        print(f"DEBUG: Attempting to write to: {log_file_path}")
        print(f"DEBUG: Log entry: {log_entry.strip()}")
        
        # Write to file
        try:
            with open(log_file_path, "a") as f:
                f.write(log_entry)
            print(f"DEBUG: Successfully wrote to emotionLog.txt")
        except Exception as e:
            print(f"Error writing to emotionLog.txt: {e}")
            print(f"DEBUG: Current working directory: {os.getcwd()}")
            print(f"DEBUG: BASE_DIR: {BASE_DIR}")
        
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
                print("Failed to read frame from camera")
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
                            
                            # Print current emotion to console
                            
                        except Exception as e:
                            self.debug_info = f"DeepFace error: {str(e)}"
                            self.current_emotion = "Detection failed"
                            self.emotion_confidence = 0.0
                            self.update_emotion_window("Detection failed")
                            self.record_emotion_data()
                            window_text, _ = self.get_window_stats()
                            print(f"Detection failed: {str(e)}")
                    else:
                        self.debug_info = "Face region is empty or too small"
                        self.current_emotion = "Face too small"
                        self.emotion_confidence = 0.0
                        self.update_emotion_window("Face too small")
                        self.record_emotion_data()
                        window_text, _ = self.get_window_stats()
                        print("Face region is empty or too small")
            else:
                self.current_emotion = "No face detected"
                self.emotion_confidence = 0.0
                self.update_emotion_window("No face detected")
                self.record_emotion_data()
                window_text, _ = self.get_window_stats()
                self.debug_info = f"No face detected in frame {frame_count}"
                print(f"No face detected in frame {frame_count}")
            
            # Control frame rate
            time.sleep(0.1)  # ~10 FPS for better window analysis
        
    def run(self):
        """Start the emotion detection process"""
        try:
            # The process_video method runs in the main thread
            # When it exits, we clean up
            self.stop_camera()
        except KeyboardInterrupt:
            print("\nStopping emotion detection...")
            self.stop_camera()

def main():
    """Main function to run the debug emotion detector"""
    print("Starting Enhanced Emotion Detection System...")
    print("This version uses a 3-second sliding window approach.")
    print("Emotion data is recorded every 3 seconds in emotionCache.")
    print("EmotionScore is calculated with weighted history.")
    print("Press Ctrl+C to stop the detection.")
    print()
    
    detector = DebugEmotionDetector()
    detector.run()

if __name__ == "__main__":
    main() 