# Worker Emotion Detection System

A real-time emotion detection system that can recognize workers and analyze their emotions using either an RTSP camera or a webcam. The system uses face detection and recognition to identify known workers and analyzes their emotional state in real-time.

## Features

- Real-time face detection and recognition
- Emotion analysis (happy, sad, angry, neutral, etc.)
- Worker database management
- Support for both RTSP cameras and webcams
- Performance optimized for real-time processing
- FPS display and performance monitoring

## Prerequisites

- Python 3.7 or higher
- Webcam or RTSP camera
- Sufficient lighting for face detection
- Stable network connection (for RTSP camera)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd worker-emotion-detection
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Webcam Version

1. Run the webcam version:
```bash
python worker_emotion_detection_webcam.py
```

2. Controls:
   - Press 'q' to quit
   - Press 'a' to add a new worker (when a face is detected)

### RTSP Camera Version

1. Run the RTSP version:
```bash
python worker_emotion_detection.py
```

2. Controls:
   - Press 'q' to quit
   - Press 'a' to add a new worker (when a face is detected)

## Adding Workers

1. Position the worker in front of the camera
2. Press 'a' when the face is clearly visible
3. Enter the worker ID when prompted
4. The system will save the face image and verify recognition

## Performance Optimization

The system includes several performance optimizations:
- Frame skipping (processes every 3rd frame)
- Rate-limited emotion analysis (twice per second)
- Optimized face detection parameters
- Efficient worker database management

## File Structure

- `worker_emotion_detection.py` - RTSP camera version
- `worker_emotion_detection_webcam.py` - Webcam version
- `worker_db/` - Directory for storing worker face data
- `requirements.txt` - Project dependencies
- `README.md` - This documentation

## Troubleshooting

### Common Issues

1. **Camera not detected**
   - Check camera connection
   - Verify camera permissions
   - Ensure no other application is using the camera

2. **RTSP Connection Issues**
   - Verify network connectivity
   - Check RTSP URL format
   - Confirm camera credentials

3. **Face Detection Problems**
   - Ensure proper lighting
   - Check camera focus
   - Verify face is clearly visible

4. **Performance Issues**
   - Reduce camera resolution
   - Close other resource-intensive applications
   - Check system resources

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenCV for face detection
- DeepFace for emotion analysis
- Dlib for face recognition 