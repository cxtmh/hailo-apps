import cv2
import io
import threading
import numpy as np
from pathlib import Path
from flask import Flask, send_file, Response, send_from_directory
from flask_socketio import SocketIO, emit, disconnect
from hailo_apps.python.core.common.core import get_logger
from .backend import Backend

# Initialize logger
logger = get_logger(__name__)

class VLMFlaskApp:
    """Flask application for VLM with WebSocket video streaming."""

    def __init__(self, camera_type: str = "usb", camera_id: int = 0):
        """
        Initialize Flask app with camera and Backend.

        Args:
            camera_type (str): Type of camera ("usb" or "rpi"). Defaults to "usb".
            camera_id (int): Camera device ID. Defaults to 0.
        """
        # Get the directory where this file is located for static files
        self.app_dir = Path(__file__).parent
        self.static_dir = self.app_dir / "static"
        
        self.app = Flask(__name__, static_folder=str(self.static_dir), static_url_path="/static")
        self.app.config['SECRET_KEY'] = 'vlm_flask_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Camera setup
        self.camera_type = camera_type
        self.camera_id = camera_id
        self.cap = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.camera_running = False

        self.picam2 = None  # For RPi camera
        self.camera_type_obj = None  # Track which camera type is being used

        # Backend (VLM inference)
        self.backend = None

        # Setup routes and WebSocket handlers
        self._setup_routes()
        self._setup_socketio()

    def initialize_camera(self):
        """Initialize camera capture."""
        try:
            if self.camera_type == "rpi":
                # Try to use picamera2 for RPi camera
                try:
                    from picamera2 import Picamera2
                    self.picam2 = Picamera2()
                    config = self.picam2.create_preview_configuration(
                        main={"size": (640, 480), "format": "RGB888"},
                        sensor={"output_size": self.picam2.sensor_resolution}  # Use full sensor
                    )
                    self.picam2.configure(config)
                    self.picam2.start()
                    logger.info("RPi camera initialized via picamera2")
                    self.camera_type_obj = "picamera2"
                except ImportError:
                    logger.error("picamera2 not installed. Install with: pip install picamera2")
                    raise
            else:  # USB camera
                self.cap = cv2.VideoCapture(self.camera_id)
                if not self.cap.isOpened():
                    raise RuntimeError(f"Failed to open USB camera at /dev/video{self.camera_id}")
                logger.info(f"USB camera initialized at /dev/video{self.camera_id}")
                
                # Set camera properties for better performance
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.camera_type_obj = "opencv"

        except Exception as e:
            logger.error(f"Camera initialization error: {e}")
            raise

    def initialize_backend(self, hef_path: str, system_prompt: str = "You are a helpful assistant that analyzes images and answers questions about them."):
        """
        Initialize VLM Backend.

        Args:
            hef_path (str): Path to the VLM HEF model.
            system_prompt (str): System prompt for VLM.
        """
        try:
            self.backend = Backend(hef_path=hef_path, system_prompt=system_prompt)
            logger.info("VLM Backend initialized")
        except Exception as e:
            logger.error(f"Backend initialization error: {e}")
            raise

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/')
        def index():
            """Serve the main HTML page."""
            html_file = self.static_dir / "index.html"
            if html_file.exists():
                with open(html_file, 'r') as f:
                    return f.read(), 200, {'Content-Type': 'text/html'}
            return "index.html not found", 404

        @self.app.route('/video')
        def video_feed():
            """Stream MJPEG video feed."""
            return Response(self._generate_mjpeg_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def _setup_socketio(self):
        """Setup WebSocket handlers."""

        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            logger.info("Client connected")
            emit('status', {'message': 'Connected to VLM Flask App'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info("Client disconnected")

        @self.socketio.on('ask')
        def handle_ask(data):
            """Handle inference request via WebSocket."""
            try:
                prompt = data.get('prompt', '')
                if not prompt:
                    emit('error', {'message': 'Empty prompt'})
                    return

                if self.backend is None:
                    emit('error', {'message': 'Backend not initialized'})
                    return

                # Get current frame
                with self.frame_lock:
                    if self.current_frame is None:
                        emit('error', {'message': 'No frame available'})
                        return
                    frame = self.current_frame.copy()

                # Run inference
                logger.info(f"Running inference with prompt: {prompt}")
                emit('status', {'message': '⏳ Processing...'})

                result = self.backend.vlm_inference(frame, prompt, timeout=30)

                # Send result back to client
                emit('result', {
                    'answer': result.get('answer', ''),
                    'time': result.get('time', '')
                })

            except Exception as e:
                logger.error(f"Inference error: {e}")
                emit('error', {'message': f'Inference error: {str(e)}'})

    def _generate_mjpeg_stream(self):
        """Generate MJPEG stream for video feed."""
        while self.camera_running:
            try:
                with self.frame_lock:
                    if self.current_frame is None:
                        continue
                    frame = self.current_frame.copy()

                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue

                # Yield frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(buffer)).encode() + b'\r\n\r\n'
                       + buffer.tobytes() + b'\r\n')

            except Exception as e:
                logger.error(f"MJPEG stream error: {e}")
                break

    def _camera_thread(self):
        """Camera capture thread."""
        logger.info("Camera thread started")
        while self.camera_running:
            try:
                if self.camera_type_obj == "picamera2":
                    frame = self.picam2.capture_array()
                else:  # OpenCV
                    ret, frame = self.cap.read()
                    if not ret:
                        logger.warning("Failed to read frame from camera")
                        continue

                with self.frame_lock:
                    self.current_frame = frame

            except Exception as e:
                logger.error(f"Camera thread error: {e}")
                break

        logger.info("Camera thread stopped")
        if self.camera_type_obj == "picamera2":
            self.picam2.stop()
        else:
            if self.cap:
                self.cap.release()

    def start(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """
        Start the Flask app and camera thread.

        Args:
            host (str): Host to listen on. Defaults to "0.0.0.0".
            port (int): Port to listen on. Defaults to 5000.
            debug (bool): Flask debug mode. Defaults to False.
        """
        try:
            # Start camera thread
            self.camera_running = True
            camera_thread = threading.Thread(target=self._camera_thread, daemon=True)
            camera_thread.start()
            logger.info("Camera thread started")

            # Start Flask app with SocketIO
            logger.info(f"Starting VLM Flask App on {host}:{port}")
            self.socketio.run(self.app, host=host, port=port, debug=debug)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.stop()
        except Exception as e:
            logger.error(f"Error starting app: {e}")
            self.stop()
            raise

    def stop(self):
        """Stop the app gracefully."""
        logger.info("Stopping VLM Flask App...")
        self.camera_running = False

        if self.backend:
            self.backend.close()

        if self.cap:
            self.cap.release()

        logger.info("VLM Flask App stopped")
