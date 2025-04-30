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
    
    print("Initializing webcam...")
    
    # Initialize video capture with webcam
    cap = cv2.VideoCapture(0)  # 0 for default webcam
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        print("Please check:")
        print("1. Webcam is connected")
        print("2. Webcam is not being used by another application")
        return
    
    # Set webcam properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height
    cap.set(cv2.CAP_PROP_FPS, 30)  # Set FPS
    
    # Get webcam properties
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Webcam properties - Resolution: {width}x{height}, FPS: {fps}")
    
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
    
    while True:
        try:
            # Read frame from webcam
            ret, frame = cap.read()
            
            if not ret:
                print("Error: Could not read frame from webcam")
                break
            
            # Increment frame counter
            frame_counter += 1
            
            # Calculate FPS
            frame_count += 1
            current_time = time.time()
            if current_time - start_time >= 1.0:
                last_fps = frame_count
                frame_count = 0
                start_time = current_time
            
            # Process every PROCESSING_INTERVAL frames
            if frame_counter % PROCESSING_INTERVAL == 0:
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                # Process each detected face
                for (x, y, w, h) in faces:
                    # Extract face region
                    face_img = frame[y:y+h, x:x+w]
                    
                    # Recognize worker
                    worker_id, confidence = detector.recognize_worker(face_img)
                    
                    # Analyze emotion if enough time has passed
                    current_time = time.time()
                    if current_time - last_emotion_time >= EMOTION_INTERVAL:
                        emotion, emotion_confidence = detector.analyze_emotion(face_img)
                        last_emotions[(x, y)] = (emotion, emotion_confidence)
                        last_emotion_time = current_time
                    
                    # Get last detected emotion for this face
                    emotion, emotion_confidence = last_emotions.get((x, y), ('unknown', 0.0))
                    
                    # Draw results on frame
                    detector.draw_results(frame, x, y, w, h, worker_id, emotion, emotion_confidence)
            
            # Display FPS
            cv2.putText(frame, f"FPS: {last_fps}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display frame
            cv2.imshow('Worker Emotion Detection', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('a'):
                # Add new worker
                worker_id = input("Enter worker ID: ")
                if worker_id:
                    # Get the first detected face
                    if len(faces) > 0:
                        x, y, w, h = faces[0]
                        face_img = frame[y:y+h, x:x+w]
                        detector.add_worker(worker_id, face_img)
                    else:
                        print("No face detected. Please position the worker in front of the camera.")
        
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            continue
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 