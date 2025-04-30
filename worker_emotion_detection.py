import cv2
import numpy as np
from deepface import DeepFace
import os
import time
from datetime import datetime

class WorkerEmotionDetector:
    def __init__(self, db_path='worker_db'):
        self.db_path = db_path
        self.known_workers = {}
        self.load_worker_database()
        
    def load_worker_database(self):
        """Load known workers' faces from the database directory"""
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
            print(f"Created worker database directory at {self.db_path}")
            print("Please add worker face images to this directory")
            return
            
        for worker_id in os.listdir(self.db_path):
            worker_dir = os.path.join(self.db_path, worker_id)
            if os.path.isdir(worker_dir):
                self.known_workers[worker_id] = worker_dir
                print(f"Loaded worker: {worker_id}")
    
    def add_worker(self, worker_id, face_img):
        """Add a new worker to the database"""
        try:
            # Verify the input image
            if face_img is None or face_img.size == 0:
                print("Error: Invalid face image provided")
                return False
                
            # Create worker directory
            worker_dir = os.path.join(self.db_path, worker_id)
            if not os.path.exists(worker_dir):
                os.makedirs(worker_dir)
                
            # Save the face image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_path = os.path.join(worker_dir, f"face_{timestamp}.jpg")
            
            # Ensure the image is in the correct format
            if len(face_img.shape) == 2:  # If grayscale
                face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2BGR)
                
            # Save the image
            success = cv2.imwrite(img_path, face_img)
            if not success:
                print(f"Error: Failed to save worker image for {worker_id}")
                return False
                
            # Verify the image was saved and can be read
            saved_img = cv2.imread(img_path)
            if saved_img is None:
                print(f"Error: Failed to read saved image for {worker_id}")
                return False
                
            # Update known workers
            self.known_workers[worker_id] = worker_dir
            print(f"Successfully added worker: {worker_id}")
            print(f"Image saved to: {img_path}")
            
            # Verify the worker can be recognized
            print("Verifying worker recognition...")
            test_id, confidence = self.recognize_worker(saved_img)
            if test_id == worker_id:
                print(f"Worker verification successful! Confidence: {confidence:.2f}")
            else:
                print("Warning: Worker verification failed. The face may not be recognizable.")
                print("This is normal for the first recognition attempt. The system will improve with more face samples.")
            
            return True
            
        except Exception as e:
            print(f"Error adding worker: {str(e)}")
            return False
    
    def recognize_worker(self, face_img):
        """Recognize if a face belongs to a known worker"""
        if not self.known_workers:
            return None, 0
            
        try:
            # Compare with all known workers
            for worker_id, worker_dir in self.known_workers.items():
                for reference_img in os.listdir(worker_dir):
                    if reference_img.endswith(('.jpg', '.jpeg', '.png')):
                        reference_path = os.path.join(worker_dir, reference_img)
                        try:
                            result = DeepFace.verify(face_img, reference_path, 
                                                   model_name='VGG-Face',
                                                   detector_backend='opencv',
                                                   enforce_detection=False,
                                                   silent=True)
                            
                            # Check if verification was successful
                            if isinstance(result, dict) and result.get('verified', False):
                                # Get confidence score, default to 0.5 if not available
                                confidence = result.get('confidence', 0.5)
                                return worker_id, confidence
                        except Exception as e:
                            print(f"Error comparing with {reference_img}: {str(e)}")
                            continue
            return None, 0
        except Exception as e:
            print(f"Error in worker recognition: {str(e)}")
            return None, 0
    
    def analyze_emotion(self, face_img):
        """Analyze emotion in a face image"""
        try:
            result = DeepFace.analyze(face_img,
                                    actions=['emotion'],
                                    enforce_detection=False,
                                    detector_backend='opencv',
                                    silent=True)
            
            # Handle both list and dictionary responses
            if isinstance(result, list):
                # If result is a list, take the first item
                result = result[0]
            
            # Get the dominant emotion and its confidence
            if isinstance(result, dict):
                dominant_emotion = result.get('dominant_emotion', 'unknown')
                emotions = result.get('emotion', {})
                confidence = emotions.get(dominant_emotion, 0.0)
                return dominant_emotion, confidence
            else:
                print(f"Unexpected result format: {type(result)}")
                return 'unknown', 0.0
                
        except Exception as e:
            print(f"Error in emotion analysis: {str(e)}")
            return 'unknown', 0.0
    
    def draw_results(self, frame, x, y, w, h, worker_id, emotion, confidence):
        """Draw bounding box and information on the frame"""
        # Draw rectangle around face
        color = (0, 255, 0) if worker_id else (255, 0, 0)  # Green for workers, Red for strangers
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        # Prepare text
        if worker_id:
            text = f"Worker {worker_id}: {emotion} ({confidence:.2f})"
        else:
            text = "Unknown"
            
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        thickness = 2
        
        # Get text size
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
        
        # Draw background rectangle for text
        margin = 4
        cv2.rectangle(frame, 
                     (x, y - text_height - 2*margin),
                     (x + text_width + 2*margin, y),
                     (0, 0, 0), -1)
        
        # Draw text
        cv2.putText(frame, text,
                    (x + margin, y - margin),
                    font, font_scale, color, thickness)

def main():
    # Initialize detector
    detector = WorkerEmotionDetector()
    
    # RTSP camera URL - exact URL that works with VLC
    rtsp_url = "rtsp://admin:Abc12345@192.168.150.142:554/Streaming/Channels/102"
    
    print("Initializing RTSP camera...")
    print(f"Connecting to: {rtsp_url}")
    
    # Configure FFMPEG options to match VLC-like behavior
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|buffer_size;1024000|max_delay;2000000|stimeout;2000000|recv_buffer_size;1024000'
    
    # Initialize video capture with FFMPEG backend
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("Error: Could not open RTSP stream")
        print("Please check:")
        print("1. Network connectivity")
        print("2. Camera IP address and port")
        print("3. Username and password")
        print("4. RTSP stream URL format")
        return
    
    # Don't set resolution/FPS - use native stream settings
    # Get stream properties
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Camera stream properties - Resolution: {width}x{height}, FPS: {fps}")
    
    # Set a larger buffer size for smoother streaming
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 4)
    
    # Initialize face cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    print("Starting worker emotion detection...")
    print("Press 'q' to quit, 'a' to add new worker")
    
    # For FPS calculation
    frame_count = 0
    start_time = time.time()
    last_fps = 0
    
    # Performance optimization parameters
    PROCESSING_INTERVAL = 3  # Process every 3rd frame
    SKIP_FRAMES = 1  # Process every frame
    frame_counter = 0
    
    # For emotion analysis rate limiting
    last_emotion_time = time.time()
    EMOTION_INTERVAL = 0.5  # Analyze emotions twice per second
    
    # Store last detected emotions
    last_emotions = {}
    
    # Add reconnection logic
    max_reconnect_attempts = 5
    reconnect_delay = 2  # seconds
    last_frame_time = time.time()
    frame_timeout = 5  # seconds
    error_count = 0
    max_errors = 10
    
    while True:
        try:
            # Read frame from RTSP stream
            ret, frame = cap.read()
            
            # Check if frame is valid
            if not ret or frame is None:
                current_time = time.time()
                if current_time - last_frame_time > frame_timeout:
                    print("Error: No frames received for too long")
                    print("Attempting to reconnect...")
                    
                    # Try to reconnect
                    for attempt in range(max_reconnect_attempts):
                        print(f"Reconnection attempt {attempt + 1}/{max_reconnect_attempts}")
                        cap.release()
                        time.sleep(reconnect_delay)
                        # Reinitialize with the same settings
                        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 4)
                        if cap.isOpened():
                            print("Successfully reconnected to RTSP stream")
                            last_frame_time = time.time()
                            error_count = 0
                            break
                        if attempt == max_reconnect_attempts - 1:
                            print("Failed to reconnect after multiple attempts. Exiting...")
                            return
                    
                    continue
                else:
                    continue
            
            last_frame_time = time.time()
            frame_counter += 1
            
            # Create processing frame (smaller version for face detection)
            processing_frame = cv2.resize(frame, (640, 360))
            
            # Detect faces using cascade classifier with optimized parameters
            gray = cv2.cvtColor(processing_frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
            
            # Scale face coordinates back to original frame size
            scale_x = frame.shape[1] / processing_frame.shape[1]
            scale_y = frame.shape[0] / processing_frame.shape[0]
            
            # Process each detected face
            for i, (x, y, w, h) in enumerate(faces):
                # Scale coordinates back to original frame size
                x = int(x * scale_x)
                y = int(y * scale_y)
                w = int(w * scale_x)
                h = int(h * scale_y)
                
                face_roi = frame[y:y+h, x:x+w]
                
                # Recognize worker
                worker_id, recognition_confidence = detector.recognize_worker(face_roi)
                
                # Rate limit emotion analysis
                current_time = time.time()
                if current_time - last_emotion_time >= EMOTION_INTERVAL:
                    # Analyze emotion for all faces
                    emotion, emotion_confidence = detector.analyze_emotion(face_roi)
                    last_emotions[i] = (emotion, emotion_confidence)
                    last_emotion_time = current_time
                    
                    # Print emotion details to console
                    if worker_id:
                        print(f"Worker {worker_id}: {emotion} ({emotion_confidence:.2f})")
                    else:
                        print(f"Unknown person: {emotion} ({emotion_confidence:.2f})")
                
                # Draw results using last known emotions
                if i in last_emotions:
                    emotion, confidence = last_emotions[i]
                    detector.draw_results(frame, x, y, w, h, worker_id, emotion, confidence)
                else:
                    detector.draw_results(frame, x, y, w, h, worker_id, None, 0)
            
            # Calculate and display FPS
            frame_count += 1
            if frame_count % 30 == 0:
                end_time = time.time()
                last_fps = 30 / (end_time - start_time)
                start_time = time.time()
                print(f"FPS: {last_fps:.2f}")
            
            # Display FPS on frame
            cv2.putText(frame, f"FPS: {last_fps:.1f}",
                        (10, frame.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Display the frame
            cv2.imshow('Worker Emotion Detection', frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('a'):
                # Add new worker
                if len(faces) > 0:
                    # Use the first detected face
                    x, y, w, h = faces[0]
                    # Scale coordinates back to original frame size
                    x = int(x * scale_x)
                    y = int(y * scale_y)
                    w = int(w * scale_x)
                    h = int(h * scale_y)
                    face_roi = frame[y:y+h, x:x+w]
                    
                    # Ensure the face region is valid
                    if face_roi.size > 0 and face_roi.shape[0] > 0 and face_roi.shape[1] > 0:
                        worker_id = input("Enter worker ID: ")
                        if worker_id.strip():  # Check if worker_id is not empty
                            print("Adding worker... Please wait while the model initializes...")
                            if detector.add_worker(worker_id, face_roi):
                                print("Worker added successfully!")
                            else:
                                print("Failed to add worker. Please try again.")
                        else:
                            print("Error: Worker ID cannot be empty")
                    else:
                        print("Error: Invalid face region detected")
                else:
                    print("No face detected. Please position a face in the camera view.")
        
        except Exception as e:
            error_count += 1
            print(f"Error processing frame: {str(e)}")
            if error_count >= max_errors:
                print("Too many errors encountered. Attempting to reconnect...")
                cap.release()
                time.sleep(reconnect_delay)
                cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                error_count = 0
            continue
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 

