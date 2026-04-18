import motor_controller
from machine import I2C, Pin
import time
import utime

gyro = None

LOOP_SPEED = 0.01

CLOCKWISE_SPEED = 800
COUNTERCLOCKWISE_SPEED = -800
NO_SPEED = 0

def motor_setup():
    # Configure motor
    motor_controller.motor_I2C_bus = I2C(0, scl=Pin(5), sda=Pin(4))
    motor_controller.motor_I2C_address = 16
    
    motor_controller.init_motor()
    
    motor_controller.set_max_acceleration(1, 800)
    motor_controller.set_max_deceleration(1, 800)
    
def wait_5_seconds():
    startTime = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), startTime) * 0.001 < 5:
        time.sleep(LOOP_SPEED)
    return True
    
cumAngle = 0
def motor_9090():
    global LOOP_SPEED, cumAngle, COUNTERCLOCKWISE_SPEED, CLOCKWISE_SPEED, NO_SPEED, gyro
    pastFirst90 = False
    startTime = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), startTime) * 0.001 < 5:
        motor_controller.set_speed(1, CLOCKWISE_SPEED)
        time.sleep(LOOP_SPEED)
        
    while utime.ticks_diff(utime.ticks_ms(), startTime) * 0.001 < 10:
        motor_controller.set_speed(1, COUNTERCLOCKWISE_SPEED)
        time.sleep(LOOP_SPEED)

motor_setup()
wait_5_seconds()
motor_9090()
