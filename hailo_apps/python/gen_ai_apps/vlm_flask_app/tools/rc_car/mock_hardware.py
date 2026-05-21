"""
Mock RC Car hardware for testing without real hardware.

Simulates PCA9685 behavior without requiring actual hardware.
"""

import logging

logger = logging.getLogger(__name__)


class MockRCCarController:
    """
    Mock RC Car controller for testing.
    
    Simulates all movements without requiring actual hardware.
    """
    
    def __init__(self, enable_mock: bool = True):
        """Initialize mock RC car controller."""
        self._enabled = enable_mock
        self._state = {
            'throttle': 'neutral',
            'steering': 'center',
        }
    
    def initialize(self):
        """Initialize the mock controller."""
        if self._enabled:
            logger.info("Mock RC Car controller initialized")
            return True
        return False
    
    def forward(self):
        """Mock move RC car forward."""
        if not self._enabled:
            return False, "Mock controller disabled"
        
        self._state['throttle'] = 'forward'
        msg = "Mock: RC car moved forward"
        logger.info(msg)
        return True, msg
    
    def backward(self):
        """Mock move RC car backward."""
        if not self._enabled:
            return False, "Mock controller disabled"
        
        self._state['throttle'] = 'backward'
        msg = "Mock: RC car moved backward"
        logger.info(msg)
        return True, msg
    
    def left(self):
        """Mock turn RC car left."""
        if not self._enabled:
            return False, "Mock controller disabled"
        
        self._state['steering'] = 'left'
        msg = "Mock: RC car turned left"
        logger.info(msg)
        return True, msg
    
    def right(self):
        """Mock turn RC car right."""
        if not self._enabled:
            return False, "Mock controller disabled"
        
        self._state['steering'] = 'right'
        msg = "Mock: RC car turned right"
        logger.info(msg)
        return True, msg
    
    def stop(self):
        """Mock stop RC car."""
        if not self._enabled:
            return False, "Mock controller disabled"
        
        self._state['throttle'] = 'neutral'
        self._state['steering'] = 'center'
        msg = "Mock: RC car stopped"
        logger.info(msg)
        return True, msg
    
    def cleanup(self):
        """Cleanup resources."""
        self._state = {'throttle': 'neutral', 'steering': 'center'}
    
    def get_state(self):
        """Get current state for testing."""
        return self._state.copy()
