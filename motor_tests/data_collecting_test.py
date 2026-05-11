from MPU6050 import MPU6050
import motor_controller
from machine import I2C, Pin
import time
import utime
import gc

gyro = None

CLOCKWISE_SPEED = 5000
COUNTERCLOCKWISE_SPEED = -5000
NO_SPEED = 0
ACTIVE_ROLL_START_THRESHOLD = 10
ACTIVE_ROLL_STOP_THRESHOLD = 2

def motor_setup():
    # Configure motor
    motor_controller.motor_I2C_bus = I2C(0, scl=Pin(5), sda=Pin(4))
    motor_controller.motor_I2C_address = 16
    
    motor_controller.init_motor()
    
    motor_controller.set_max_acceleration(1, 5000)
    motor_controller.set_max_deceleration(1, 5000)

def gyro_setup():
    global gyro
    i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
    gyro = MPU6050(i2c=i2c)
    gyro.reset()
    time.sleep(1)
    gyro._set_defaults()
    gyro.wake()
    gyro._set_power_defaults2(0b000000)
    #inverts accelX (up) and gyroX(roll) - see top comments on roll values
    gyro.set_inv_measures(0b100100)
    time.sleep(0.5)
    gyro.calibration_test(0, 0)

cumAngle = 0
def data_collect():
    global gyro, cumAngle, CLOCKWISE_SPEED, COUNTERCLOCKWISE_SPEED, NO_SPEED
    with open("data.csv", "w") as f:
        f.write(f"speed,time from speed start, delta roll\n")
        for speed in range(CLOCKWISE_SPEED, 0, -100):
            startTime = utime.ticks_ms()
            curTime = utime.ticks_ms()
            while utime.ticks_diff(curTime, startTime) * 0.001 < 10:
                motor_controller.set_speed(1, speed)
                curTime = utime.ticks_ms()
                f.write(f"{speed},{utime.ticks_diff(curTime, startTime)},{gyro.get_gyroX()}\n")
                time.sleep(0.01)
            time.sleep(0.1)
            motor_controller.set_speed(1, NO_SPEED)
            time.sleep(0.1)
            gc.collect()
            f.flush()

motor_setup()
gyro_setup()
data_collect()