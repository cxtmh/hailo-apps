# VLM Flask App with RC Car Control

A web-based Vision Language Model (VLM) application with agent tool calling. Streams live camera feed and accepts natural language commands to control an RC car via LLM with tools. Provides a browser-accessible interface for real-time image understanding + hardware control on Hailo-10H.

## Features

✨ **Real-Time Video Streaming**
- Live MJPEG video feed from USB or Raspberry Pi cameras
- Low-latency browser-based visualization with HTML5

🤖 **LLM Agent with Tool Calling**
- Run LLM on Hailo-10H for reasoning and tool selection
- Parse tool calls and execute RC car movements
- Full agent loop: LLM → tool call → execute → continue

🎮 **RC Car Control**
- Control RC car via PCA9685 PWM module
- Actions: forward, backward, left, right, stop
- Natural language commands: "Move closer to the chair"
- Mock hardware mode for testing without hardware

🌐 **Web-Based Interface**
- Modern, responsive HTML5 UI with dark mode support
- Chat-like interface for commands and responses
- WebSocket for bidirectional real-time communication

📱 **Flexible Input**
- USB camera support (auto-detection)
- Raspberry Pi camera support (libcamera)
- Real or mock RC car hardware
- Customizable system prompts

## Installation

### Prerequisites

- Hailo-10H accelerator installed and configured
- Python 3.10+
- USB or Raspberry Pi camera connected
- **(Optional) RC Car Hardware:**
  - PCA9685 PWM controller (I2C address 0x40 by default)
  - RC car with motor (throttle on channel 1) and servo (steering on channel 0)
  - Raspberry Pi or desktop with I2C support
  - Note: Can use mock hardware for testing without real hardware

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

### RC Car Control (Optional)

The app includes an RC car control tool that the LLM can invoke based on natural language commands.

#### Using Mock Hardware (for testing)

```bash
export RC_CAR_MOCK=true
python3 hailo_apps/python/gen_ai_apps/vlm_flask_app/vlm_flask_app.py --input usb
```

#### Using Real Hardware (PCA9685 + RC Car)

**Wiring:**
- PCA9685 Channel 0: Steering servo (PWM)
- PCA9685 Channel 1: Motor ESC (PWM)
- PCA9685 Power: 5V and GND
- I2C: SCL (GPIO 3), SDA (GPIO 2) on Raspberry Pi

**Commands:**
```bash
# No environment variable = use real hardware
python3 hailo_apps/python/gen_ai_apps/vlm_flask_app/vlm_flask_app.py --input usb
```

**Testing RC Car:**
```bash
# Send command: "move forward"
# LLM will call rc_car tool with action="forward"
# Car will move forward on channel 1
```

#### Supported RC Car Commands

The LLM will recognize these natural language commands:
- "move the car forward"
- "go back" / "move backward"
- "turn left"
- "turn right"
- "stop the car"
- "move closer to the red chair" (forward implied)

#### Hardware Notes

**Verified (tested):**
- Motor forward (channel 1, 1800 µs)
- Motor backward (channel 1, 1200 µs)
- Stop (both channels, 1500 µs neutral)

**Untested (use with caution):**
- Steering left (channel 0, 1300 µs)
- Steering right (channel 0, 1700 µs)

## Architecture

```
Browser Client                    Flask Server                 Hailo-10H
┌──────────────────┐            ┌─────────────────────┐       ┌───────────┐
│ HTML5 Canvas     │────────────│ /video endpoint     │
│                  │ MJPEG      │                     │
│ Chat Interface   │◄──────────│ WebSocket Handler   │       │ LLM       │
│                  │ WebSocket  │                     │       │ Backend   │
└──────────────────┘ (command)  │ Camera Thread       │──────│           │
                   (response)   │ (frame capture)     │ ────→│ VDevice   │
                                │                     │◄────│ + Model   │
                                │ Tool Execution      │       └───────────┘
                                │ (RC car commands)   │
                                │                     │       ┌───────────┐
                                │ PCA9685 Control─────────→│ RC Car:   │
                                └─────────────────────┘       │ Motor +   │
                                                              │ Servo     │
                                                              └───────────┘
```

### Component Descriptions

- **HTML5 Canvas**: Displays MJPEG stream from `/video` endpoint (runs continuously)
- **Chat Interface**: WebSocket client for sending commands and receiving responses
- **MJPEG Stream** (`/video`): Live video feed encoded as JPEG frames
- **WebSocket Handler**: Receives user commands, calls backend.agent_inference()
- **Camera Thread**: Background thread capturing frames from USB/RPi camera
- **Agent Backend**: Multiprocessing LLM inference with tool calling
  - Initializes LLM model on Hailo-10H VDevice
  - Discovers and loads RC car tool
  - Implements agent loop: LLM → parse tools → execute → continue
- **Tool Execution**: Invokes rc_car tool methods (forward, backward, left, right, stop)
- **RC Car Control**: PCA9685 PWM module controls motor and steering servo

## WebSocket Protocol

### Client → Server

**Send Command:**
```json
{
  "prompt": "Move the car forward to get closer to the chair"
}
```

### Server → Client

**Status Update:**
```json
{
  "message": "⏳ Processing..."
}
```

**Agent Result (with tool calls):**
```json
{
  "answer": "I'll move the car forward to get a closer look at the chair.",
  "time": "3.45 seconds",
  "tools_made": ["rc_car"]
}
```

**Error:**
```json
{
  "message": "Error: Failed to process command"
}
```

### Agent Response Details

- **answer**: Final text response from the LLM
- **time**: Total processing time including LLM inference and tool execution
- **tools_made**: List of tool names invoked (e.g., ["rc_car"] if car moved)

## Configuration

### Application Settings

Edit the constants in `vlm_flask_app.py` to customize behavior:

```python
MAX_TOKENS = 200                 # Max LLM output tokens
TEMPERATURE = 0.1               # Sampling temperature (lower = more deterministic)
SEED = 42                        # Random seed for reproducibility
SYSTEM_PROMPT = "..."            # System instruction for LLM (guides tool usage)
```

### Environment Variables

```bash
# Use mock RC car hardware (for testing)
export RC_CAR_MOCK=true

# Use real hardware (default if not set)
unset RC_CAR_MOCK
```

### Backend Initialization

The Flask app initializes the agent backend with:
- `enable_agent=True`: Enable LLM agent with tool calling
- `tools_dir`: Auto-detects tools/ directory for tool discovery
- System prompt guides LLM to use RC car tool for movement commands

## RC Car Tool Troubleshooting

### Tool Not Invoked

**Issue**: LLM doesn't call rc_car tool even when asked to move the car.

**Solutions**:
1. Check system prompt includes tool instruction (see Configuration)
2. Try explicit commands: "move the car forward" instead of "advance"
3. Check LLM is running in agent mode (`enable_agent=True` in backend)

### PCA9685 Not Detected

**Error**: `Failed to initialize MotorController: [I2C error]`

**Solutions**:
1. Verify I2C is enabled:
   ```bash
   sudo raspi-config  # On RPi
   i2cdetect -y 1    # List I2C devices
   ```
2. Check PCA9685 I2C address is 0x40:
   ```bash
   i2cdetect -y 1 | grep 40
   ```
3. Verify wiring: SDA (GPIO 2), SCL (GPIO 3)
4. Use mock mode for testing:
   ```bash
   export RC_CAR_MOCK=true
   ```

### Car Doesn't Move

**Issue**: Tool executes but car stays still.

**Solutions**:
1. **Steering untested**: Left/right may not work yet (untested hardware path)
2. **Check motor connection**: Verify channel 1 is connected to motor ESC
3. **Verify PWM signals**: Use oscilloscope or PWM tester on channel 0/1
4. **Check battery**: Ensure motor has sufficient power

### Mock Hardware Not Working

**Error**: `Could not import MockRCCarController`

**Solution**:
- Ensure `tools/rc_car/mock_hardware.py` exists
- Re-run: `python3 vlm_flask_app.py --input usb` (without RC_CAR_MOCK if error)

## General Troubleshooting

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
