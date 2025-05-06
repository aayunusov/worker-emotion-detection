import cv2
import numpy as np
from deepface import DeepFace
import os
import time
from datetime import datetime
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('worker_emotion_detection.log')
    ]
)

class EmotionDatabase:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="emotion_detection",
            user="postgres",
            password="postgres",
            host="localhost"
        )
        self.cursor = self.conn.cursor()
        self.last_store_time = time.time()
        self.store_interval = 60  # Store data every 60 seconds
        
    def store_emotion_data(self, worker_id, emotion, confidence, frame):
        current_time = time.time()
        
        # Check if it's time to store data (every minute)
        if current_time - self.last_store_time >= self.store_interval:
            try:
                # Save the frame only if it's a recognized worker or no face detected
                if worker_id != "unknown":
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    if worker_id == "none":
                        frame_path = f"emotion_frames/no_face_{timestamp}.jpg"
                    else:
                        frame_path = f"emotion_frames/{worker_id}_{timestamp}.jpg"
                    cv2.imwrite(frame_path, frame)
                
                # Store in database
                self.cursor.execute(
                    "INSERT INTO emotion_data (worker_id, emotion, confidence, timestamp, frame_path) VALUES (%s, %s, %s, %s, %s)",
                    (worker_id, emotion, confidence, datetime.now(), frame_path)
                )
                self.conn.commit()
                
                self.last_store_time = current_time
                logging.info(f"Stored emotion data for {worker_id}: {emotion} ({confidence:.2f})")
                
            except Exception as e:
                logging.error(f"Error storing emotion data: {str(e)}")
                self.conn.rollback()
    
    def close(self):
        self.cursor.close()
        self.conn.close()

class WorkerEmotionDetector:
    def __init__(self, db_path='worker_db'):
        self.db_path = db_path
        self.known_workers = {}
        self.db = EmotionDatabase()
        self.load_worker_database()
        
    def load_worker_database(self):
        """Load known workers' faces from the database directory"""
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
            logging.info(f"Created worker database directory at {self.db_path}")
            logging.info("Please add worker face images to this directory")
            return
            
        for worker_id in os.listdir(self.db_path):
            worker_dir = os.path.join(self.db_path, worker_id)
            if os.path.isdir(worker_dir):
                self.known_workers[worker_id] = worker_dir
                logging.info(f"Loaded worker: {worker_id}")
    
    def add_worker(self, worker_id, face_img):
        """Add a new worker to the database"""
        try:
            # Verify the input image
            if face_img is None or face_img.size == 0:
                logging.error("Invalid face image provided")
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
                logging.error(f"Failed to save worker image for {worker_id}")
                return False
                
            # Verify the image was saved and can be read
            saved_img = cv2.imread(img_path)
            if saved_img is None:
                logging.error(f"Failed to read saved image for {worker_id}")
                return False
                
            # Update known workers
            self.known_workers[worker_id] = worker_dir
            logging.info(f"Successfully added worker: {worker_id}")
            logging.info(f"Image saved to: {img_path}")
            
            # Verify the worker can be recognized
            logging.info("Verifying worker recognition...")
            test_id, confidence = self.recognize_worker(saved_img)
            if test_id == worker_id:
                logging.info(f"Worker verification successful! Confidence: {confidence:.2f}")
            else:
                logging.warning("Worker verification failed. The face may not be recognizable.")
                logging.warning("This is normal for the first recognition attempt. The system will improve with more face samples.")
            
            return True
            
        except Exception as e:
            logging.error(f"Error adding worker: {str(e)}")
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
                            logging.error(f"Error comparing with {reference_img}: {str(e)}")
                            continue
            return None, 0
        except Exception as e:
            logging.error(f"Error in worker recognition: {str(e)}")
            return None, 0
    
    def analyze_emotion(self, face_img):
        """Analyze emotion in a face image"""
        try:
            result = DeepFace.analyze(face_img,
                                    actions=['emotion'],
                                    enforce_detection=False,
                                    detector_backend='opencv',
                                    silent=True)
            
            if isinstance(result, list):
                result = result[0]
            
            if isinstance(result, dict):
                emotions = result.get('emotion', {})
                # Focus only on angry, neutral, and happy
                angry = emotions.get('angry', 0.0)
                neutral = emotions.get('neutral', 0.0)
                happy = emotions.get('happy', 0.0)
                
                # Find the highest confidence among the three emotions
                if angry > neutral and angry > happy:
                    return 'angry', angry
                elif happy > neutral and happy > angry:
                    return 'happy', happy
                else:
                    return 'neutral', neutral
            return 'neutral', 0.0
                
        except Exception as e:
            logging.error(f"Error in emotion analysis: {str(e)}")
            return 'neutral', 0.0
    
def process_frame(frame, emotion_detector, face_recognizer, emotion_db):
    try:
        # Create a smaller frame for face detection
        small_frame = cv2.resize(frame, (640, 360))
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100),
            maxSize=(300, 300)
        )
        
        logging.info(f"Detected {len(faces)} faces in the frame")
        
        if len(faces) == 0:
            # Store data when no faces are detected
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            frame_path = f"emotion_frames/no_face_{timestamp}.jpg"
            cv2.imwrite(frame_path, frame)
            
            # Store in database with null values
            emotion_db.store_emotion_data(
                worker_id="none",
                emotion="none",
                confidence=0.0,
                frame=frame
            )
            logging.info("Stored frame with no face detection")
            return
        
        # Scale face coordinates back to original frame size
        scale_x = frame.shape[1] / small_frame.shape[1]
        scale_y = frame.shape[0] / small_frame.shape[0]
        
        # Process each detected face
        for (x, y, w, h) in faces:
            # Scale coordinates back to original frame size
            x = int(x * scale_x)
            y = int(y * scale_y)
            w = int(w * scale_x)
            h = int(h * scale_y)
            
            # Extract face region
            face_roi = frame[y:y+h, x:x+w]
            
            # Recognize worker
            worker_id, worker_confidence = face_recognizer.recognize_worker(face_roi)
            if worker_id is not None:
                logging.info(f"Recognized worker: {worker_id} with confidence: {worker_confidence:.2f}")
                # Analyze emotion
                emotion, emotion_confidence = emotion_detector.analyze_emotion(face_roi)
                logging.info(f"Detected emotion: {emotion} with confidence: {emotion_confidence:.2f}")
                
                # Store data in database
                emotion_db.store_emotion_data(worker_id, emotion, emotion_confidence, frame)
                logging.info(f"Stored data for {worker_id}: {emotion} ({emotion_confidence:.2f})")
            else:
                logging.info("No worker recognized in the detected face")
                # Store data for unrecognized face
                emotion_db.store_emotion_data(
                    worker_id="unknown",
                    emotion="none",
                    confidence=0.0,
                    frame=frame
                )
                logging.info("Stored data for unrecognized face")
    except Exception as e:
        logging.error(f"Error processing frame: {str(e)}")

def process_rtsp_stream(rtsp_url, emotion_detector, face_recognizer, emotion_db):
    cap = None
    last_frame_time = time.time()
    reconnect_attempts = 0
    max_reconnect_attempts = 5
    reconnect_delay = 5  # seconds
    frame_count = 0

    # Configure FFMPEG options for better stability
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|buffer_size;1024000|max_delay;2000000|stimeout;2000000|recv_buffer_size;1024000|rtsp_flags;prefer_tcp'
    
    while True:
        try:
            if cap is None or not cap.isOpened():
                if reconnect_attempts >= max_reconnect_attempts:
                    logging.error("Max reconnection attempts reached. Exiting...")
                    break
                
                logging.info(f"Attempting to connect to RTSP stream (attempt {reconnect_attempts + 1}/{max_reconnect_attempts})")
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                if not cap.isOpened():
                    raise Exception("Failed to open RTSP stream")
            
                # Set capture properties for better stability
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 8)
                cap.set(cv2.CAP_PROP_FPS, 25)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                
                reconnect_attempts = 0
                logging.info("Successfully connected to RTSP stream")

            ret, frame = cap.read()
            if not ret:
                logging.error("Failed to read frame from RTSP stream")
                    cap.release()
                    cap = None
                reconnect_attempts += 1
                time.sleep(reconnect_delay)
                continue

            # Reset reconnect attempts on successful frame read
            reconnect_attempts = 0
            frame_count += 1

            # Process frame every minute
            current_time = time.time()
            if current_time - last_frame_time >= 60:  # Every 60 seconds
                logging.info(f"Processing frame {frame_count} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                process_frame(frame, emotion_detector, face_recognizer, emotion_db)
                last_frame_time = current_time
                logging.info(f"Next frame processing scheduled for {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_frame_time + 60))}")
                
        except Exception as e:
            logging.error(f"Error processing RTSP stream: {str(e)}")
            if cap is not None:
                cap.release()
                cap = None
            reconnect_attempts += 1
            time.sleep(reconnect_delay)

    if cap is not None:
        cap.release()

def main():
    # Initialize detector
    emotion_detector = WorkerEmotionDetector()
    face_recognizer = WorkerEmotionDetector()
    emotion_db = EmotionDatabase()

    # RTSP URL
    rtsp_url = "rtsp://admin:Abc12345@192.168.150.116:554/Streaming/Channels/102"

    try:
        logging.info("Starting emotion detection system...")
        process_rtsp_stream(rtsp_url, emotion_detector, face_recognizer, emotion_db)
    except KeyboardInterrupt:
        logging.info("Stopping emotion detection system...")
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
    finally:
        emotion_db.close()

if __name__ == "__main__":
    main() 

