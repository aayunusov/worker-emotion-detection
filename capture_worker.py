import cv2
import os
import time
from datetime import datetime
import logging
import subprocess
from worker_emotion_detection import WorkerEmotionDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('capture_worker.log')
    ]
)

def test_rtsp_connection(rtsp_url):
    """Test if RTSP stream is accessible"""
    try:
        cmd = ['ffmpeg', '-i', rtsp_url, '-t', '1', '-f', 'null', '-']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return "Stream #0:0: Video" in result.stderr
    except Exception as e:
        logging.error(f"Error testing RTSP connection: {str(e)}")
        return False

def capture_from_rtsp(rtsp_url):
    """Capture frames from RTSP stream"""
    # Test RTSP connection first
    if not test_rtsp_connection(rtsp_url):
        logging.error("Could not connect to RTSP stream")
        return None
    
    logging.info("Successfully connected to RTSP stream")
    
    # Configure OpenCV capture
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp'  # Try TCP instead of UDP
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        logging.error("Error: Could not open RTSP stream with OpenCV")
        return None
    
    # Set capture properties
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer size
    cap.set(cv2.CAP_PROP_FPS, 25)
    
    # Initialize face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    logging.info("Press 's' to capture when a face is detected, 'q' to quit")
    preview_counter = 0
    
    while True:
        # Read multiple frames to get the latest one
        for _ in range(5):
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
        
        if not ret or frame is None:
            logging.error("Error: Could not read frame from RTSP stream")
            time.sleep(1)
            continue
        
        # Create a smaller frame for face detection
        small_frame = cv2.resize(frame, (640, 360))
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100),
            maxSize=(300, 300)
        )
        
        # Scale face coordinates back to original frame size
        scale_x = frame.shape[1] / small_frame.shape[1]
        scale_y = frame.shape[0] / small_frame.shape[0]
        
        # Draw rectangles around faces and save preview
        preview_frame = frame.copy()
        for (x, y, w, h) in faces:
            x = int(x * scale_x)
            y = int(y * scale_y)
            w = int(w * scale_x)
            h = int(h * scale_y)
            cv2.rectangle(preview_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Save preview image with counter
        preview_path = f'preview_{preview_counter}.jpg'
        cv2.imwrite(preview_path, preview_frame)
        logging.info(f"Preview saved as {preview_path}")
        preview_counter = (preview_counter + 1) % 5  # Keep only last 5 previews
        
        # Check for user input
        key = input("Press 's' to capture, 'q' to quit: ").lower()
        
        if key == 's' and len(faces) > 0:
            # Get the first detected face
            x, y, w, h = faces[0]
            x = int(x * scale_x)
            y = int(y * scale_y)
            w = int(w * scale_x)
            h = int(h * scale_y)
            
            # Extract face region with margin
            margin = int(min(w, h) * 0.2)  # 20% margin
            y1 = max(0, y - margin)
            y2 = min(frame.shape[0], y + h + margin)
            x1 = max(0, x - margin)
            x2 = min(frame.shape[1], x + w + margin)
            face_roi = frame[y1:y2, x1:x2]
            
            if face_roi.size > 0:
                # Save the captured face for verification
                cv2.imwrite('captured_face.jpg', face_roi)
                logging.info("Face captured and saved as captured_face.jpg")
                cap.release()
                return face_roi
            else:
                logging.error("Invalid face region detected")
        elif key == 'q':
            logging.info("Capture cancelled")
            cap.release()
            return None
    
    cap.release()
    return None

def main():
    # RTSP camera URL
    rtsp_url = "rtsp://admin:Abc12345@192.168.150.116:554/Streaming/Channels/102"
    
    # Initialize detector
    detector = WorkerEmotionDetector()
    
    while True:
        # Ask for worker ID
        worker_id = input("\nEnter worker ID (or 'q' to quit): ").strip()
        
        if worker_id.lower() == 'q':
            break
            
        if not worker_id:
            logging.error("Worker ID cannot be empty")
            continue
            
        # Capture face from RTSP stream
        logging.info(f"\nCapturing face for worker {worker_id}...")
        face_img = capture_from_rtsp(rtsp_url)
        
        if face_img is not None:
            # Add worker to database
            if detector.add_worker(worker_id, face_img):
                logging.info(f"Successfully added worker {worker_id} to the database")
            else:
                logging.error(f"Failed to add worker {worker_id}")
        
        # Ask if user wants to add another worker
        choice = input("\nAdd another worker? (y/n): ").lower()
        if choice != 'y':
            break
    
    logging.info("Worker addition process completed")
    
    # Cleanup preview files
    for i in range(5):
        preview_file = f'preview_{i}.jpg'
        if os.path.exists(preview_file):
            os.remove(preview_file)

if __name__ == "__main__":
    main() 