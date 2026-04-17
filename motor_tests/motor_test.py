from machine import Pin, I2C
import time
import motor_controller

def motor_setup():
    # Configure motor
    motor_controller.motor_I2C_bus = I2C(0, scl=Pin(5), sda=Pin(4))
    motor_controller.motor_I2C_address = 16
    
    motor_controller.init_motor()
    
    motor_controller.set_max_acceleration(1, 800)
    motor_controller.set_max_deceleration(1, 800)

led = Pin(25, Pin.OUT)
def blink():
    led.toggle()
    
motor_setup()
    
while True:
    blink()
    motor_controller.set_speed(1, -800)
    time.sleep(3)
    motor_controller.set_speed(1, 800)
    time.sleep(3)