from MPU6050 import MPU6050
import motor_controller
from machine import I2C, Pin
import time
import utime

gyro = None

LOOP_SPEED = 0.01

LAUNCH_THRESHOLD = 2

CLOCKWISE_SPEED = 800
COUNTERCLOCKWISE_SPEED = -800
NO_SPEED = 0
ACTIVE_ROLL_START_THRESHOLD = 10
ACTIVE_ROLL_STOP_THRESHOLD = 2

def motor_setup():
    # Configure motor
    motor_controller.motor_I2C_bus = I2C(0, scl=Pin(5), sda=Pin(4))
    motor_controller.motor_I2C_address = 16
    
    motor_controller.init_motor()
    
    motor_controller.set_max_acceleration(1, 800)
    motor_controller.set_max_deceleration(1, 800)

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
    #gyro.calibration_test(0, 0)
    
def until_launched():
    launch_counter = 0
    while True:
        #if up accel is greater than 2 g's
        if gyro.get_accelX() > LAUNCH_THRESHOLD:
            launch_counter += 1
            if launch_counter > 2:
                return True
    #should be unreachable
    return False

cumAngle = 0
def motor_stable():
    global gyro, LOOP_SPEED, cumAngle, CLOCKWISE_SPEED, COUNTERCLOCKWISE_SPEED, NO_SPEED, ACTIVE_ROLL_START_THRESHOLD, ACTIVE_ROLL_STOP_THRESHOLD
    activeRolling = False
    startTime = utime.ticks_ms()
    while True:
        if utime.ticks_diff(utime.ticks_ms(), startTime) * 0.001 > 20:
            time.sleep(0.5)
            motor_controller.set_speed(1, NO_SPEED)
            break
        deltaTime = LOOP_SPEED
        deltaRoll = gyro.get_gyroX()
        cumAngle += deltaRoll * deltaTime
        if cumAngle > ACTIVE_ROLL_START_THRESHOLD:
            motor_controller.set_speed(1, COUNTERCLOCKWISE_SPEED)
            activeRolling = True
        elif cumAngle < -ACTIVE_ROLL_START_THRESHOLD:
            motor_controller.set_speed(1, CLOCKWISE_SPEED)
            activeRolling = True
        else:
            if activeRolling:
                if cumAngle > ACTIVE_ROLL_STOP_THRESHOLD:
                    motor_controller.set_speed(1, COUNTERCLOCKWISE_SPEED)
                elif cumAngle < -ACTIVE_ROLL_STOP_THRESHOLD:
                    motor_controller.set_speed(1, CLOCKWISE_SPEED)
                else:
                    activeRolling = False
                    motor_controller.set_speed(1, NO_SPEED)
            else:
                motor_controller.set_speed(1, NO_SPEED)
        time.sleep(LOOP_SPEED)
                
motor_setup()
gyro_setup()
until_launched()
motor_stable()