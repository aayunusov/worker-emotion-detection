import cv2
import numpy as np
from deepface import DeepFace
import os
import time
from datetime import datetime
import sqlite3

# Define emotion labels - only the ones we care about
emotion_labels = ['angry', 'happy', 'neutral']


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

def initialize_database():
    """Initialize the SQLite database for storing emotion data"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'worker_emotions.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing table if it exists
    cursor.execute('DROP TABLE IF EXISTS worker_emotions')
    
    # Create new table with correct structure
    cursor.execute('''
    CREATE TABLE worker_emotions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id TEXT NOT NULL,
        emotion_type TEXT NOT NULL,
        emotion_percentage REAL NOT NULL,
        recorded_datetime TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    return conn

def store_emotion_data(conn, worker_id, emotion_type, emotion_percentage):
    """Store emotion data in the database"""
    cursor = conn.cursor()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
    INSERT INTO worker_emotions (worker_id, emotion_type, emotion_percentage, recorded_datetime)
    VALUES (?, ?, ?, ?)
    ''', (worker_id, emotion_type, emotion_percentage, current_time))
    
    conn.commit()

def recognize_worker(face_img, known_workers):
    """Try to recognize if the face belongs to a known worker"""
    try:
        for worker_id in known_workers:
            worker_dir = os.path.join('worker_db', worker_id)
            for reference_img in os.listdir(worker_dir):
                if reference_img.endswith(('.jpg', '.jpeg', '.png')):
                    reference_path = os.path.join(worker_dir, reference_img)
                    try:
                        result = DeepFace.verify(face_img, reference_path, 
                                               model_name='VGG-Face',
                                               detector_backend='opencv',
                                               enforce_detection=False,
                                               silent=True)
                        
                        if result['verified']:
                            return worker_id, result['distance']
                    except Exception as e:
                        continue
        return None, None
    except Exception as e:
        print(f"Error in worker recognition: {str(e)}")
        return None, None

def register_worker(frame, face_detector):
    # Convert frame to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    if len(faces) == 0:
        print("No face detected. Please position the worker in front of the camera.")
        return None
    
    # Get the first detected face
    x, y, w, h = faces[0]
    face_roi = frame[y:y+h, x:x+w]
    
    # Get worker ID from user
    worker_id = input("Enter worker ID: ").strip()
    if not worker_id:
        print("Invalid worker ID")
        return None
    
    try:
        # Save worker's face image to worker_db folder
        worker_dir = os.path.join('worker_db', worker_id)
        if not os.path.exists(worker_dir):
            os.makedirs(worker_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        face_path = os.path.join(worker_dir, f"face_{timestamp}.jpg")
        cv2.imwrite(face_path, face_roi)
        
        print(f"Worker {worker_id} registered successfully!")
        print(f"Face image saved to: {face_path}")
        return worker_id
        
    except Exception as e:
        print(f"Error registering worker: {str(e)}")
        return None

def process_frame(frame, face_detector, known_workers, db_conn):
    # Convert frame to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    # Process each detected face
    for (x, y, w, h) in faces:
        # Extract face ROI
        face_roi = frame[y:y+h, x:x+w]
        
        # Try to recognize the worker
        worker_id, confidence = recognize_worker(face_roi, known_workers)
        
        if worker_id is not None:
            try:
                # Analyze emotion using DeepFace
                result = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)
                
                # Get only the emotions we care about
                emotions = result[0]['emotion']
                relevant_emotions = {emotion: emotions[emotion] for emotion in ['angry', 'happy', 'neutral']}
                
                # Calculate total of relevant emotions
                total = sum(relevant_emotions.values())
                
                # Get the emotion with highest probability and calculate its percentage
                emotion_name = max(relevant_emotions, key=relevant_emotions.get)
                emotion_percentage = (relevant_emotions[emotion_name] / total) * 100 if total > 0 else 0
                
                # Store emotion data in database
                store_emotion_data(db_conn, worker_id, emotion_name, emotion_percentage)
                
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Display worker ID and emotion
                text = f"{worker_id}: {emotion_name} ({emotion_percentage:.1f}%)"
                cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
            except Exception as e:
                print(f"Error processing face: {str(e)}")
                continue
        else:
            # Draw rectangle around unknown face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    
    return frame

def main():
    # Initialize face detector
    face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Initialize database
    db_conn = None
    cap = None
    try:
        db_conn = initialize_database()
        
        # Load existing workers from worker_db folder
        known_workers = []
        for worker_id in os.listdir('worker_db'):
            worker_dir = os.path.join('worker_db', worker_id)
            if os.path.isdir(worker_dir):
                known_workers.append(worker_id)
                print(f"Found existing worker: {worker_id}")
        
        # Open webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return
        
        # Set webcam properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        print("\nPress 'a' to add new worker")
        print("Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame from webcam")
                break
                
            # Process frame
            frame = process_frame(frame, face_detector, known_workers, db_conn)
            
            # Display frame
            cv2.imshow('Worker Emotion Detection', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nQuitting program...")
                break
            elif key == ord('a'):
                new_worker = register_worker(frame, face_detector)
                if new_worker:
                    known_workers.append(new_worker)
    
    except Exception as e:
        print(f"Error in main loop: {str(e)}")
    
    finally:
        # Cleanup
        print("\nCleaning up resources...")
        if db_conn is not None:
            try:
                db_conn.close()
            except Exception as e:
                print(f"Error closing database: {str(e)}")
        
        if cap is not None:
            try:
                cap.release()
            except Exception as e:
                print(f"Error releasing webcam: {str(e)}")
        
        try:
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"Error closing windows: {str(e)}")
        
        print("Program terminated successfully.")

if __name__ == "__main__":
    main() 