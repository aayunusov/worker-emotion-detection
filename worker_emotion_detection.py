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
            print(f"Error in emotion analysis: {str(e)}")
            return 'neutral', 0.0
    
    def draw_results(self, frame, x, y, w, h, worker_id, emotion, confidence):
        """Draw bounding box and information on the frame"""
        # Draw rectangle around face
        color = (0, 255, 0)  # Green for all faces
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        # Prepare text
        text = f"{worker_id}: {emotion} ({confidence:.2f})"
            
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
    rtsp_url = "rtsp://admin:Abc12345@192.168.150.116:554/Streaming/Channels/102"
    
    print("\n=== Worker Emotion Detection System ===")
    print("Initializing RTSP camera...")
    print(f"Connecting to: {rtsp_url}")
    
    # Configure FFMPEG options to match VLC-like behavior
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|buffer_size;1024000|max_delay;2000000|stimeout;2000000|recv_buffer_size;1024000|rtsp_flags;prefer_tcp'
    
    # Initialize video capture with FFMPEG backend
    cap = None
    max_connection_attempts = 5
    connection_delay = 3
    
    for attempt in range(max_connection_attempts):
        try:
            print(f"\nConnection attempt {attempt + 1}/{max_connection_attempts}")
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            # Set additional capture properties for better stability
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 8)
                cap.set(cv2.CAP_PROP_FPS, 25)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                
                # Test the connection
                test_frames = 0
                max_test_frames = 5
                while test_frames < max_test_frames:
                    ret, _ = cap.read()
                    if ret:
                        test_frames += 1
                    else:
                        break
                
                if test_frames == max_test_frames:
                    print("✓ Camera connection established and verified")
                    break
                else:
                    print("✗ Camera connection test failed")
                    cap.release()
                    cap = None
            
            if attempt < max_connection_attempts - 1:
                print(f"Retrying in {connection_delay} seconds...")
                time.sleep(connection_delay)
                
        except Exception as e:
            print(f"Error during connection attempt {attempt + 1}: {str(e)}")
            if cap is not None:
                cap.release()
                cap = None
            if attempt < max_connection_attempts - 1:
                time.sleep(connection_delay)
    
    if not cap or not cap.isOpened():
        print("\nError: Could not establish stable camera connection")
        return
    
    # Initialize face cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    print("\n=== System Ready ===")
    print("Commands:")
    print("- Press 'a' to add a new worker")
    print("- Press 'q' to quit")
    print("===================\n")
    
    # Performance optimization parameters
    PROCESSING_INTERVAL = 3  # Process every 3rd frame
    SKIP_FRAMES = 1  # Process every frame
    frame_counter = 0
    
    # For emotion analysis rate limiting
    last_emotion_time = time.time()
    EMOTION_INTERVAL = 1.0  # Analyze emotions once per second
    
    # Store last detected emotions
    last_emotions = {}
    
    # Add reconnection logic
    max_reconnect_attempts = 5
    reconnect_delay = 3
    last_frame_time = time.time()
    frame_timeout = 3
    error_count = 0
    max_errors = 10
    
    # Performance optimization: Pre-allocate frame arrays
    processing_frame = np.zeros((360, 640, 3), dtype=np.uint8)
    gray_frame = np.zeros((360, 640), dtype=np.uint8)
    
    # Create a named window for better key handling
    cv2.namedWindow('Worker Emotion Detection', cv2.WINDOW_NORMAL)
    
    # Flag to track if we're in add worker mode
    is_adding_worker = False
    face_detected = False
    face_roi = None
    
    try:
        while True:
            try:
                # Read frame from RTSP stream
                ret, frame = cap.read()
                
                # Check if frame is valid
                if not ret or frame is None:
                    current_time = time.time()
                    if current_time - last_frame_time > frame_timeout:
                        print("\nError: No frames received for too long")
                        print("Attempting to reconnect...")
                        
                        # Try to reconnect
                        for attempt in range(max_reconnect_attempts):
                            print(f"Reconnection attempt {attempt + 1}/{max_reconnect_attempts}")
                            cap.release()
                            time.sleep(reconnect_delay)
                            
                            # Reinitialize with the same settings
                            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                            if cap.isOpened():
                                cap.set(cv2.CAP_PROP_BUFFERSIZE, 8)
                                cap.set(cv2.CAP_PROP_FPS, 25)
                                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                                
                                # Test the reconnection
                                test_frames = 0
                                max_test_frames = 3
                                while test_frames < max_test_frames:
                                    ret, _ = cap.read()
                                    if ret:
                                        test_frames += 1
                                    else:
                                        break
                                
                                if test_frames == max_test_frames:
                                    print("✓ Successfully reconnected to RTSP stream")
                                    last_frame_time = time.time()
                                    error_count = 0
                                    break
                                else:
                                    print("✗ Reconnection test failed")
                                    cap.release()
                                    cap = None
                            
                            if attempt == max_reconnect_attempts - 1:
                                print("Failed to reconnect after multiple attempts. Exiting...")
                                return
                        
                        continue
                    else:
                        continue
                
                last_frame_time = time.time()
                frame_counter += 1
                
                # Skip frames for better performance
                if frame_counter % PROCESSING_INTERVAL != 0:
                    continue
                
                # Create processing frame (smaller version for face detection)
                cv2.resize(frame, (640, 360), dst=processing_frame)
                
                # Detect faces using cascade classifier with optimized parameters
                cv2.cvtColor(processing_frame, cv2.COLOR_BGR2GRAY, dst=gray_frame)
                faces = face_cascade.detectMultiScale(
                    gray_frame,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(100, 100),
                    maxSize=(300, 300),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
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
                    
                    # Additional validation for face detection
                    face_roi = frame[y:y+h, x:x+w]
                    if face_roi.size == 0 or face_roi.shape[0] < 100 or face_roi.shape[1] < 100:
                        continue  # Skip invalid face regions
                    
                    # If in add worker mode, store the face ROI
                    if is_adding_worker:
                        face_detected = True
                        # Draw green rectangle around the face
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, "Press 's' to capture", (x, y-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        break
                    
                    # Check if this is a known worker
                    worker_id, worker_confidence = detector.recognize_worker(face_roi)
                    if worker_id is None:
                        continue  # Skip unknown faces
                    
                    # Rate limit emotion analysis
                    current_time = time.time()
                    if current_time - last_emotion_time >= EMOTION_INTERVAL:
                        # Analyze emotion for known workers only
                        emotion, emotion_confidence = detector.analyze_emotion(face_roi)
                        last_emotions[i] = (emotion, emotion_confidence)
                        last_emotion_time = current_time
                        
                        # Print worker and emotion details to console
                        print(f"Worker {worker_id}: {emotion} ({emotion_confidence:.2f})")
                    
                    # Draw results using last known emotions
                    if i in last_emotions:
                        emotion, confidence = last_emotions[i]
                        detector.draw_results(frame, x, y, w, h, worker_id, emotion, confidence)
                    else:
                        detector.draw_results(frame, x, y, w, h, worker_id, 'neutral', 0)
                
                # Display the frame
                cv2.imshow('Worker Emotion Detection', frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\nQuitting program...")
                    break
                elif key == ord('a') and not is_adding_worker:
                    is_adding_worker = True
                    face_detected = False
                    print("\n=== Adding New Worker ===")
                    print("Please position the worker's face in the camera view...")
                    print("Press 's' to capture the face, or 'q' to cancel")
                elif key == ord('s') and is_adding_worker and face_detected:
                    # Show preview of the face to be captured
                    preview = face_roi.copy()
                    cv2.putText(preview, "Press 'y' to confirm, 'n' to retry", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.imshow('Face Preview', preview)
                    
                    # Wait for confirmation
                    confirm_key = cv2.waitKey(0) & 0xFF
                    cv2.destroyWindow('Face Preview')
                    
                    if confirm_key == ord('y'):
                        # Ask for worker ID
                        print("\nEnter worker ID and press Enter (or press Enter to cancel):")
                        worker_id = input("Worker ID: ").strip()
                        
                        if worker_id:
                            print(f"\nAdding worker {worker_id}...")
                            # Add the worker
                            if detector.add_worker(worker_id, face_roi):
                                print(f"✓ Worker {worker_id} added successfully!")
                                print("The worker will be recognized in future sessions.")
                            else:
                                print("✗ Failed to add worker. Please try again.")
                        else:
                            print("✗ Worker ID cannot be empty. Operation cancelled.")
                    elif confirm_key == ord('n'):
                        print("Retrying face capture...")
                        continue
                    else:
                        print("✗ Operation cancelled.")
                    
                    is_adding_worker = False
                    face_detected = False
                    print("=== Press 'a' again to add another worker ===\n")
                
            except Exception as e:
                error_count += 1
                print(f"\nError processing frame: {str(e)}")
                if error_count >= max_errors:
                    print("Too many errors encountered. Attempting to reconnect...")
                    cap.release()
                    time.sleep(reconnect_delay)
                    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                    error_count = 0
                continue
    
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    finally:
        # Cleanup
        print("\nCleaning up resources...")
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("Program terminated successfully.")

if __name__ == "__main__":
    main() 

