from MPU6050 import MPU6050
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
    
cumAngle = 0
def motor_9090():
    global LOOP_SPEED, cumAngle, COUNTERCLOCKWISE_SPEED, CLOCKWISE_SPEED, NO_SPEED, gyro
    pastFirst90 = False
    while True:
        deltaTime = LOOP_SPEED
        deltaRoll = gyro.get_gyroX()
        cumAngle += deltaRoll * deltaTime
        if deltaRoll >= 0:
            ...
            #communicates what the system is trying to do to cameras
            #wireless.send("ROLL_CW")
        else:
            ...
            #communicates what the system is trying to do to cameras
            #wireless.send("ROLL_CCW")
        if not pastFirst90:
            if cumAngle > 95:
                pastFirst90 = True
                motor_controller.set_speed(1, COUNTERCLOCKWISE_SPEED)
            else:
                motor_controller.set_speed(1, CLOCKWISE_SPEED)
        else:
            if cumAngle < -100:
                #hopefully ensures this command doesn't get lost due to the speed
                #at which commands are sent
                time.sleep(0.1)
                motor_controller.set_speed(1, NO_SPEED)
                break
            else:
                motor_controller.set_speed(1, COUNTERCLOCKWISE_SPEED)
        time.sleep(LOOP_SPEED)

motor_setup()
gyro_setup()
motor_9090()