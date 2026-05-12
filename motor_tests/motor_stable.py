from MPU6050 import MPU6050
import motor_controller
from machine import I2C, Pin
import time
import utime

gyro = None

def motor_setup():
    # Configure motor
    motor_controller.motor_I2C_bus = I2C(0, scl=Pin(5), sda=Pin(4))
    motor_controller.motor_I2C_address = 16
    
    motor_controller.init_motor()
    
    motor_controller.set_timeout_time(300) #ms
    
    #as fast as possible
    motor_controller.set_max_acceleration(1, 0)
    motor_controller.set_max_deceleration(1, 0)

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
    
def get_motor_speed_from_roll(roll):
    return -0.004 * roll
    
def motor_stable():
    global gyro
    cum_motor_speed = 0
    cum_roll = 0
    start_time_ms = utime.ticks_ms()
    cur_time_ms = utime.ticks_ms()
    roll_check = -1
    while utime.ticks_diff(cur_time_ms, start_time_ms) < 30000:
        prev_time_ms = cur_time_ms
        cur_time_ms = utime.ticks_ms()
        delta_roll = gyro.get_gyroX()
        delta_time = utime.ticks_diff(cur_time_ms, prev_time_ms)
        cum_roll += delta_roll * delta_time / 1000
        #every 250 milliseconds drive the motor - gives it time to adjust
        if utime.ticks_diff(cur_time_ms, start_time_ms) // 250 > roll_check:
            roll_check += 1
            cum_motor_speed += get_motor_speed_from_roll(delta_roll)
            #fastest direction to go to get back to 0
            min_from_zero = (cum_roll % 360) - 180
            cum_motor_speed += min_from_zero * -0.1 #return to 0
            motor_controller.set_speed(1, cum_motor_speed)
        #record data here

motor_setup()
gyro_setup()
motor_stable()