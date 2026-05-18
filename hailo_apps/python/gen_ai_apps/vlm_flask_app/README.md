# VLM Flask App

A web-based Vision Language Model (VLM) application that streams live camera feed and accepts natural language questions via WebSocket. Provides a browser-accessible interface for real-time image understanding on Hailo-10H.

## Features

✨ **Real-Time Video Streaming**
- Live MJPEG video feed from USB or Raspberry Pi cameras
- Low-latency browser-based visualization with HTML5

🤖 **VLM Inference**
- Run Qwen2-VL or other VLM models on Hailo-10H
- Ask natural language questions about the camera feed
- Streaming token output for real-time feedback

🌐 **Web-Based Interface**
- Modern, responsive HTML5 UI with dark mode support
- Chat-like interface for user questions and VLM responses
- WebSocket for bidirectional real-time communication

📱 **Flexible Input**
- USB camera support (auto-detection)
- Raspberry Pi camera support (libcamera)
- Customizable system prompts

## Installation

### Prerequisites

- Hailo-10H accelerator installed and configured
- Python 3.10+
- USB or Raspberry Pi camera connected

### Setup

1. **Navigate to hailo-apps directory:**
   ```bash
   cd /path/to/hailo-apps
   ```

2. **Activate virtual environment:**
   ```bash
   source setup_env.sh
   ```

3. **Install Flask dependencies (first time only):**
   ```bash
   pip install -r hailo_apps/python/gen_ai_apps/vlm_flask_app/requirements.txt
   ```

   Or install alongside the main package:
   ```bash
   pip install Flask==2.3.0 Flask-SocketIO==5.3.0 python-socketio==5.9.0 python-engineio==4.7.0
   ```

4. **(Optional) Install the package:**
   ```bash
   pip install -e .
   ```

## Usage

### USB Camera (Auto-Detection)

```bash
python3 hailo_apps/python/gen_ai_apps/vlm_flask_app/vlm_flask_app.py --input usb
```

### Raspberry Pi Camera

```bash
python3 hailo_apps/python/gen_ai_apps/vlm_flask_app/vlm_flask_app.py --input rpi
```

### Custom Port

```bash
python3 hailo_apps/python/gen_ai_apps/vlm_flask_app/vlm_flask_app.py --input usb --port 8080
```

### Custom HEF Model

```bash
python3 hailo_apps/python/gen_ai_apps/vlm_flask_app/vlm_flask_app.py --input usb --hef-path /path/to/custom_model.hef
```

### Access the Web UI

Once the app starts, open your browser and navigate to:
```
http://localhost:5000
```

## Architecture

```
Browser Client                           Flask Server              Hailo-10H
┌──────────────────┐                    ┌──────────────────┐      ┌─────────┐
│ HTML5 Canvas     │──── MJPEG stream ──│ /video endpoint  │
│                  │                    │                  │
│ Chat Interface   │◄─── WebSocket ────│ /ws endpoint     │      │ VLM     │
│                  │   (ask/result)     │                  │      │ Backend │
└──────────────────┘                    │ Camera Thread    │────→ │         │
                                        │ + Backend        │◄──── │ VDevice │
                                        └──────────────────┘      │ + Model │
                                                                  └─────────┘
```

### Component Descriptions

- **HTML5 Canvas**: Displays MJPEG stream from `/video` endpoint
- **Chat Interface**: WebSocket client for sending questions and receiving responses
- **MJPEG Stream** (`/video`): Continuous video feed encoded as JPEG frames
- **WebSocket Handler** (`/ws`): Bidirectional communication for Q&A
- **Camera Thread**: Background thread capturing frames from USB/RPi camera
- **Backend**: Multiprocessing VLM inference (unchanged from vlm_chat)

## WebSocket Protocol

### Client → Server

**Ask a Question:**
```json
{
  "action": "ask",
  "prompt": "What is in this image?"
}
```

### Server → Client

**Status Update:**
```json
{
  "message": "⏳ Processing..."
}
```

**Result:**
```json
{
  "answer": "This is a person walking in a park...",
  "time": "2.34 seconds"
}
```

**Error:**
```json
{
  "message": "Error: Failed to process image"
}
```

## Configuration

Edit the constants in `vlm_flask_app.py` to customize behavior:

```python
MAX_TOKENS = 200                 # Max VLM output tokens
TEMPERATURE = 0.1               # Sampling temperature (lower = more deterministic)
SEED = 42                        # Random seed for reproducibility
SYSTEM_PROMPT = "..."            # System instruction for VLM
INFERENCE_TIMEOUT = 60           # Timeout for inference (seconds)
```

## Troubleshooting

### USB Camera Not Detected

**Error:** `No USB camera found for '--input usb'`

**Solutions:**
1. Check if camera is plugged in and recognized:
   ```bash
   ls /dev/video*
   ```
2. Try specifying the device directly:
   ```bash
   python3 vlm_flask_app.py --input /dev/video0
   ```
3. Check permissions:
   ```bash
   sudo usermod -a -G video $USER
   newgrp video
   ```

### RPi Camera Not Detected

**Error:** `Failed to open RPi camera`

**Solutions:**
1. Enable libcamera in Raspberry Pi configuration:
   ```bash
   sudo raspi-config
   # Navigate to Interface Options > Camera > Enable
   ```
2. Test libcamera:
   ```bash
   libcamera-hello --list-cameras
   ```

### Port Already in Use

**Error:** `Address already in use`

**Solutions:**
1. Use a different port:
   ```bash
   python3 vlm_flask_app.py --input usb --port 8080
   ```
2. Kill existing process:
   ```bash
   lsof -i :5000
   kill -9 <PID>
   ```

### VLM Model Not Found

**Error:** `Failed to resolve HEF path for VLM model`

**Solutions:**
1. Download the model explicitly:
   ```bash
   python3 -c "from hailo_apps.python.core.common.core import resolve_hef_path; resolve_hef_path(None, 'vlm_flask_app', 'hailo10h')"
   ```
2. Specify model path directly:
   ```bash
   python3 vlm_flask_app.py --input usb --hef-path /usr/local/hailo/resources/models/Qwen2-VL-2B-Instruct.hef
   ```

### Slow Performance / High Latency

**Causes:**
- Multiprocessing overhead
- Network congestion
- Camera resolution too high

**Solutions:**
1. Ensure only one instance is running
2. Close other applications
3. Use wired network connection if accessing remotely
4. Lower camera resolution in `app.py`:
   ```python
   self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
   self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
   ```

## Differences from vlm_chat

| Feature | vlm_chat | vlm_flask_app |
|---------|----------|---------------|
| Interface | Terminal UI (OpenCV window) | Browser-based Web UI |
| Access | Local terminal only | Browser (localhost or network) |
| Streaming | Real-time token output to stdout | WebSocket response objects |
| Interaction | State machine (capture → question → result) | Continuous chat interface |
| Backend | Same multiprocessing VLM backend | Same multiprocessing VLM backend |
| Video Input | USB or RPi camera | USB or RPi camera |
| Output Format | Terminal text | JSON over WebSocket |

## Advanced Usage

### Running Behind a Reverse Proxy

To expose the app on a different domain (e.g., via nginx):

1. **Configure nginx:**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

2. **Start the app:**
   ```bash
   python3 vlm_flask_app.py --input usb
   ```

### Running Multiple Instances

Each instance requires its own port:

```bash
# Terminal 1
python3 vlm_flask_app.py --input usb --port 5000

# Terminal 2
python3 vlm_flask_app.py --input rpi --port 5001
```

### Adding HTTPS/SSL

For secure remote access, use a reverse proxy or add SSL directly:

```python
# In vlm_flask_app.py main()
self.app.start(host="0.0.0.0", port=port, ssl_context=('cert.pem', 'key.pem'))
```

## Performance Notes

- **MJPEG Stream**: ~10-30 fps depending on resolution and network
- **VLM Inference**: 2-30 seconds per query (depends on max_tokens and model)
- **Latency**: Single-threaded processing queue (one inference at a time)
- **Memory**: ~2-4 GB (VLM model + inference buffers)

## Future Enhancements

- [ ] Multiple concurrent users (requires VDevice load balancing)
- [ ] WebRTC streaming (reduces latency, better compression)
- [ ] Authentication and API keys
- [ ] Inference history / logging
- [ ] Custom system prompt via UI
- [ ] Adjustable quality/latency trade-offs
- [ ] Prometheus metrics for monitoring

## Related Apps

- [vlm_chat](../vlm_chat/) — Terminal-based VLM application
- [llm_chat](../llm_chat/) — LLM chat application
- [whisper_chat](../whisper_chat/) — Speech-to-text application
- [voice_assistant](../voice_assistant/) — Voice assistant with TTS

## License

Same as hailo-apps repository.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review [CONTRIBUTING.md](../../../CONTRIBUTING.md)
3. Open an issue on GitHub
