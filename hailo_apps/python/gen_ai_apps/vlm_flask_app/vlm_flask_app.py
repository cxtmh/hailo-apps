#!/usr/bin/env python3
"""
VLM Flask App - Flask-based VLM application with WebSocket video streaming.

A web-based Vision Language Model application that streams live camera feed
and accepts questions via WebSocket. Provides a browser-accessible UI for
real-time image understanding.

Usage:
    python3 vlm_flask_app.py --input usb [--hef-path /path/to/model.hef]
    python3 vlm_flask_app.py --input rpi [--port 5000]

Features:
    - Live MJPEG video streaming from USB or RPi camera
    - Real-time VLM inference via WebSocket
    - Browser-based HTML5 UI
    - Graceful shutdown on Ctrl+C
"""

import sys
import signal
import logging
import os
from pathlib import Path

# Add repo root to path for imports
repo_root = None
for p in Path(__file__).resolve().parents:
    if (p / "hailo_apps" / "config" / "config_manager.py").exists():
        repo_root = p
        break
if repo_root is not None:
    sys.path.insert(0, str(repo_root))

from hailo_apps.python.core.common.core import (
    get_standalone_parser,
    get_logger,
    handle_list_models_flag,
    resolve_hef_path,
)
from hailo_apps.python.core.common.camera_utils import get_usb_video_devices
from hailo_apps.python.core.gstreamer.gstreamer_helper_pipelines import get_source_type
from hailo_apps.python.core.common.defines import (
    VLM_FLASK_APP,
    VLM_MODEL_NAME_H10,
    HAILO10H_ARCH,
    RPI_NAME_I,
    USB_CAMERA,
)
from hailo_apps.python.gen_ai_apps.vlm_flask_app.app import VLMFlaskApp

# Configuration Constants
MAX_TOKENS = 200
TEMPERATURE = 0.1
SEED = 42
SYSTEM_PROMPT = "You are a helpful assistant that analyzes images and answers questions about them."

# Initialize logger
logger = get_logger(__name__)


class VLMFlaskAppCLI:
    """CLI wrapper for VLM Flask App."""

    def __init__(self):
        """Initialize the CLI wrapper."""
        self.app = None
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Handle interrupt signals."""
        logger.info("Signal received, shutting down...")
        self.stop()

    def stop(self):
        """Stop the application."""
        if self.app:
            self.app.stop()
        sys.exit(0)

    def run(self, args):
        """
        Run the VLM Flask App.

        Args:
            args: Parsed command-line arguments.
        """
        try:
            # Resolve HEF path
            hef_path = resolve_hef_path(
                args.hef_path if hasattr(args, "hef_path") else None,
                app_name=VLM_FLASK_APP,
                arch=HAILO10H_ARCH,
            )
            if hef_path is None:
                logger.error("Failed to resolve HEF path for VLM model.")
                sys.exit(1)

            logger.info(f"Using HEF model: {hef_path}")

            # Handle input source
            video_source = args.input
            if video_source == USB_CAMERA:
                logger.debug("USB_CAMERA detected; scanning USB devices...")
                usb_devices = get_usb_video_devices()
                if not usb_devices:
                    logger.error("No USB camera found for '--input usb'")
                    print(
                        'Provided argument "--input" is set to "usb", '
                        "however no available USB cameras found. "
                        "Please connect a camera or specify different input method."
                    )
                    sys.exit(1)
                else:
                    logger.info(f"Using USB camera: {usb_devices[0]}")
                    video_source = usb_devices[0]

            # Determine source type
            source_type = (
                get_source_type(video_source) if video_source is not None else None
            )

            if video_source is None:
                print(
                    'Please provide an input source using the "--input" argument: '
                    '"usb" for USB camera or "rpi" for Raspberry Pi camera.'
                )
                sys.exit(1)

            logger.info(f"Using input source: {video_source} (type: {source_type})")

            # Initialize Flask app
            logger.info("Initializing VLM Flask App...")
            self.app = VLMFlaskApp(camera_type=source_type, camera_id=video_source)

            # Initialize camera
            logger.info("Initializing camera...")
            self.app.initialize_camera()

            # Initialize backend
            logger.info("Initializing VLM backend...")
            self.app.initialize_backend(
                hef_path=str(hef_path), system_prompt=SYSTEM_PROMPT
            )

            # Get Flask app port
            port = getattr(args, "port", 5000)
            logger.info(f"Starting Flask app on port {port}...")
            print(f"\n{'='*70}")
            print(f"  VLM Flask App started successfully!")
            print(f"  Open your browser and navigate to: http://localhost:{port}")
            print(f"  Press Ctrl+C to stop the app")
            print(f"{'='*70}\n")

            # Start Flask app (blocking call)
            self.app.start(host="0.0.0.0", port=port, debug=False)

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            self.stop()
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            self.stop()


def main():
    """Main entry point."""
    # Create argument parser
    parser = get_standalone_parser()

    # Add Flask-specific arguments
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to listen on (default: 5000)",
    )

    # Handle --list-models flag
    handle_list_models_flag(parser, VLM_FLASK_APP)

    # Parse arguments
    args = parser.parse_args()

    # Create and run CLI wrapper
    cli = VLMFlaskAppCLI()
    cli.run(args)


if __name__ == "__main__":
    main()
