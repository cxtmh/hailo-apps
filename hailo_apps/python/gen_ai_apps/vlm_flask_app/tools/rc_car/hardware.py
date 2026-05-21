"""
RC Car hardware interface using PCA9685 and MotorController.

Wraps the verified MotorController from sample_motor_code.
Can fall back to mock hardware if real hardware is unavailable.
"""

import logging
import os
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

# Check if mock mode is enabled via environment variable
USE_MOCK_HARDWARE = os.environ.get('RC_CAR_MOCK', 'false').lower() == 'true'

# Import MotorController from sample_motor_code
MotorController = None
if not USE_MOCK_HARDWARE:
    try:
        # Add parent directory to path for imports
        vlm_flask_app_dir = Path(__file__).parent.parent.parent
        sample_motor_code_dir = vlm_flask_app_dir / "sample_motor_code"
        if str(sample_motor_code_dir) not in sys.path:
            sys.path.insert(0, str(sample_motor_code_dir))
        
        from motor_controller import MotorController
    except ImportError as e:
        logger.warning(f"Could not import MotorController: {e}")
        logger.info("Falling back to mock hardware")
        MotorController = None

# Import mock hardware if needed
if MotorController is None or USE_MOCK_HARDWARE:
    try:
        from .mock_hardware import MockRCCarController
        logger.info("Using mock RC car hardware")
        USE_MOCK = True
    except ImportError as e:
        logger.error(f"Could not import MockRCCarController: {e}")
        MockRCCarController = None
        USE_MOCK = False
else:
    MockRCCarController = None
    USE_MOCK = False


class RCCarController:
    """
    RC Car controller using PCA9685 or mock hardware.
    
    Real Hardware:
    - Verified methods (tested): forward(), backward(), stop()
    - Untested methods: left(), right()
    
    Mock Hardware:
    - All methods simulated for testing without hardware
    """
    
    def __init__(self):
        """Initialize RC car controller."""
        self.controller = None
        self._initialized = False
        self._error_message = None
        self._use_mock = False
    
    def initialize(self):
        """Initialize the motor controller (real or mock)."""
        if self._initialized:
            return True
        
        # Try real hardware first
        if MotorController is not None and not USE_MOCK_HARDWARE:
            try:
                self.controller = MotorController()
                self.controller.initialize()
                self._initialized = True
                self._use_mock = False
                logger.info("RC Car controller initialized with real hardware")
                return True
            except Exception as e:
                logger.warning(f"Failed to initialize real hardware: {e}")
                logger.info("Falling back to mock hardware")
        
        # Fall back to mock hardware
        if MockRCCarController is not None or USE_MOCK_HARDWARE:
            try:
                self.controller = MockRCCarController(enable_mock=True)
                self.controller.initialize()
                self._initialized = True
                self._use_mock = True
                logger.info("RC Car controller initialized with mock hardware")
                return True
            except Exception as e:
                self._error_message = f"Failed to initialize mock controller: {str(e)}"
                logger.error(self._error_message)
                return False
        
        self._error_message = "No hardware controller available"
        logger.error(self._error_message)
        return False
    
    def forward(self):
        """Move RC car forward."""
        if not self._initialized:
            if not self.initialize():
                return False, self._error_message
        
        try:
            if self._use_mock:
                return self.controller.forward()
            else:
                self.controller.throttle_forward()
                logger.info("RC car moved forward")
                return True, "RC car moved forward"
        except Exception as e:
            error_msg = f"Failed to move forward: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def backward(self):
        """Move RC car backward."""
        if not self._initialized:
            if not self.initialize():
                return False, self._error_message
        
        try:
            if self._use_mock:
                return self.controller.backward()
            else:
                self.controller.throttle_backward()
                logger.info("RC car moved backward")
                return True, "RC car moved backward"
        except Exception as e:
            error_msg = f"Failed to move backward: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def left(self):
        """Turn RC car left (steering only)."""
        if not self._initialized:
            if not self.initialize():
                return False, self._error_message
        
        try:
            if self._use_mock:
                return self.controller.left()
            else:
                self.controller.steer_left()
                logger.warning("RC car turned left (steering untested)")
                return True, "RC car turned left"
        except Exception as e:
            error_msg = f"Failed to turn left: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def right(self):
        """Turn RC car right (steering only)."""
        if not self._initialized:
            if not self.initialize():
                return False, self._error_message
        
        try:
            if self._use_mock:
                return self.controller.right()
            else:
                self.controller.steer_right()
                logger.warning("RC car turned right (steering untested)")
                return True, "RC car turned right"
        except Exception as e:
            error_msg = f"Failed to turn right: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def stop(self):
        """Stop RC car (throttle to neutral, steering to center)."""
        if not self._initialized:
            if not self.initialize():
                return False, self._error_message
        
        try:
            if self._use_mock:
                return self.controller.stop()
            else:
                self.controller.stop()
                logger.info("RC car stopped")
                return True, "RC car stopped"
        except Exception as e:
            error_msg = f"Failed to stop: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def cleanup(self):
        """Cleanup resources."""
        if self.controller:
            try:
                self.stop()
            except Exception as e:
                logger.debug(f"Error during cleanup: {e}")
        self._initialized = False
