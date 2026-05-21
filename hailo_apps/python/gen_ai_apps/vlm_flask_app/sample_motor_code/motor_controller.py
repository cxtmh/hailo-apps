from adafruit_pca9685 import PCA9685
import busio
import board

# Channel assignments
STEERING_CHANNEL = 0
THROTTLE_CHANNEL = 1

# Pulse width ranges (in microseconds)
STEERING_CENTER_US = 1500
STEERING_LEFT_US = 1300
STEERING_RIGHT_US = 1700

THROTTLE_NEUTRAL_US = 1500
THROTTLE_FORWARD_US = 1800
THROTTLE_BACKWARD_US = 1200

class MotorController:
    def __init__(self):
        """Initialize I2C and PCA9685."""
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c)
        self.pca.frequency = 50  # 50Hz for RC servo/ESC
    
    def set_pulse(self, channel, pulse_us):
        """
        Set PWM pulse width in microseconds.
        PCA9685 uses 12-bit duty cycle (0-65535).
        Convert microseconds to duty cycle value.
        """
        duty_cycle = int((pulse_us / 20000.0) * 65535)
        self.pca.channels[channel].duty_cycle = duty_cycle
        print(f"  Channel {channel}: {pulse_us}µs -> duty_cycle {duty_cycle}")
    
    def steer_left(self):
        print(f"LEFT: Setting steering to {STEERING_LEFT_US}µs")
        self.set_pulse(STEERING_CHANNEL, STEERING_LEFT_US)
    
    def steer_right(self):
        print(f"RIGHT: Setting steering to {STEERING_RIGHT_US}µs")
        self.set_pulse(STEERING_CHANNEL, STEERING_RIGHT_US)
    
    def throttle_forward(self):
        print(f"FORWARD: Setting throttle to {THROTTLE_FORWARD_US}µs")
        self.set_pulse(THROTTLE_CHANNEL, THROTTLE_FORWARD_US)
    
    def throttle_backward(self):
        print(f"BACKWARD: Setting throttle to {THROTTLE_BACKWARD_US}µs")
        self.set_pulse(THROTTLE_CHANNEL, THROTTLE_BACKWARD_US)
    
    def stop(self):
        print(f"STOP: Setting throttle to neutral {THROTTLE_NEUTRAL_US}µs")
        print(f"STOP: Setting steering to center {STEERING_CENTER_US}µs")
        self.set_pulse(THROTTLE_CHANNEL, THROTTLE_NEUTRAL_US)
        self.set_pulse(STEERING_CHANNEL, STEERING_CENTER_US)
    
    def initialize(self):
        """Initialize ESC and steering servo with neutral signals."""
        self.set_pulse(THROTTLE_CHANNEL, THROTTLE_NEUTRAL_US)
        self.set_pulse(STEERING_CHANNEL, STEERING_CENTER_US)