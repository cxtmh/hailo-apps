"""
RC Car control tool for LLM agent.

Allows the LLM to control the RC car via natural language commands.
"""

import logging
from typing import Any

from .hardware import RCCarController

logger = logging.getLogger(__name__)

# Tool metadata
name: str = "move"

display_description: str = (
    "Control RC car: move forward, backward, turn left, or turn right."
)

description: str = (
    "RC car control tool. Use this when the user asks to move, turn, drive, "
    "navigate, or steer the RC car. "
    "Actions available: forward, backward, left, right, stop. "
    "Examples: 'move the car forward', 'turn left', 'get closer to the chair', "
    "'back up', 'stop the car'. "
    "CRITICAL: If the user's request is unclear or doesn't specify a valid direction, "
    "use default=true to ask for clarification rather than guessing."
)

# Initialize controller only when tool is selected
_rc_car_controller = None
_initialized = False


def initialize_tool() -> None:
    """Initialize RC car controller when tool is selected."""
    global _rc_car_controller, _initialized
    if not _initialized:
        try:
            _rc_car_controller = RCCarController()
            if _rc_car_controller.initialize():
                _initialized = True
                logger.info("RC car controller initialized")
            else:
                logger.warning("RC car controller initialization failed")
                _initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize RC car controller: {e}")
            _initialized = True


def cleanup_tool() -> None:
    """Clean up RC car controller resources."""
    global _rc_car_controller, _initialized
    if _rc_car_controller is not None:
        try:
            _rc_car_controller.cleanup()
        except Exception as e:
            logger.debug(f"Error during RC car cleanup: {e}")
    _initialized = False
    _rc_car_controller = None


def _get_rc_car_controller() -> RCCarController:
    """Get RC car controller instance, initializing if needed."""
    global _rc_car_controller
    if not _initialized:
        initialize_tool()
    return _rc_car_controller


schema: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["forward", "backward", "left", "right", "stop"],
            "description": "Direction/action to move the RC car. Required unless 'default' is used.",
        },
        "default": {
            "type": "boolean",
            "description": "Set to true if the request is unclear or doesn't specify a valid action. "
                          "The tool will return a clarification message.",
        },
    },
    "required": [],  # Neither action nor default required due to conditional logic
}


def run(**kwargs) -> dict[str, Any]:
    """
    Execute RC car control action.

    Args:
        **kwargs: Contains 'action' (forward/backward/left/right/stop) or 'default' (true).

    Returns:
        dict: Tool result with 'ok' and either 'result' or 'error'.
    """
    action = kwargs.get("action", "").strip().lower()
    use_default = kwargs.get("default", False)

    # Handle default case (unclear request)
    if use_default:
        return {
            "ok": True,
            "error": "Please clarify which direction you'd like to move: forward, backward, left, right, or stop?",
        }

    # Validate action
    valid_actions = ["forward", "backward", "left", "right", "stop"]
    if not action:
        return {
            "ok": False,
            "error": f"Missing action. Valid actions: {', '.join(valid_actions)}",
        }

    if action not in valid_actions:
        return {
            "ok": False,
            "error": f"Invalid action '{action}'. Valid actions: {', '.join(valid_actions)}",
        }

    # Get controller
    controller = _get_rc_car_controller()
    if controller is None:
        return {
            "ok": False,
            "error": "RC car controller not available",
        }

    # Execute action
    try:
        if action == "forward":
            success, message = controller.forward()
        elif action == "backward":
            success, message = controller.backward()
        elif action == "left":
            success, message = controller.left()
        elif action == "right":
            success, message = controller.right()
        elif action == "stop":
            success, message = controller.stop()
        else:
            success, message = False, f"Unexpected action: {action}"

        if success:
            return {"ok": True, "result": message}
        else:
            return {"ok": False, "error": message}

    except Exception as e:
        error_msg = f"Error executing action '{action}': {str(e)}"
        logger.error(error_msg)
        return {"ok": False, "error": error_msg}
