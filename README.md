# Worker Emotion Detection System

A real-time emotion detection system that can recognize workers and analyze their emotions using either an RTSP camera or a webcam. The system uses face detection and recognition to identify known workers and analyzes their emotional state in real-time.

## Dataset collection bot

A private Telegram bot asks a consenting adult to pose seven expressions and send two new photos of each. The prompt is the label. Photos are saved only on the computer that runs the bot:

```text
dataset/P0001/meta.json
dataset/P0001/neutral_01.jpg
dataset/P0001/neutral_02.jpg
dataset/P0001/happy_01.jpg
...
dataset/registry.json
dataset/bot.log
```

`dataset/` is gitignored. The bot does not upload it. Set `DATASET_DIR` in `.env` if the files should go to another disk. Saved JPEGs are re-encoded, so phone location data is not kept. Names are not asked.

### Launch

1. In Telegram, open `@BotFather`, send `/newbot`, and copy the token.
2. Copy `.env.example` to `.env` and paste the token as `TELEGRAM_BOT_TOKEN`.
3. Install and start the bot on the computer that should keep the photos:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-bot.txt
python -m collection_bot
```

The terminal prints the folder it is writing to. Leave that process running. On Windows, activate the venv with `venv\Scripts\activate`.

4. On your phone, open the bot, send `/start`, and finish one session yourself (14 photos). Then check that `dataset/P0001/` contains the JPEGs and `meta.json`.
5. Share the bot link. Each person works in a private chat. Commands: `/start`, `/delete`, `/cancel`.
6. While it is running, `python -m collection_bot.status` prints the counts. After collection, `python -m collection_bot.export` writes `dataset/manifest.csv`. That file contains Telegram ids. Keep the whole `dataset/` folder private, and copy it to a backup disk at the end of the day.

Restarting the program does not lose photos. The next photo or button continues that person's session, and `/start` resumes it too. `/delete` removes their folder.

Install `requirements-bot.txt` for this bot. `requirements.txt` is the older camera system and pulls in TensorFlow and dlib, which this bot does not use.

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