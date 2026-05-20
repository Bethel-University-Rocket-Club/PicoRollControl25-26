from MPU6050 import MPU6050
import motor_controller
from machine import I2C, Pin
import time
import utime
import wireless
import os

gyro = None

data_file = None

APOGEE = 0
APOGEE_UPDATE_TIME = 0
LAUNCH_TIME_MS = 0
LAUNCH_THRESHOLD = 2 #g's

MOTOR_STILL = 0

def sd_card_setup():
    global data_file
    data_file = open("data.csv", "w")
    data_file.write(f"time from launch,intended roll direction,cumulative roll,delta roll,motor speed\n")

def wireless_setup():
    wireless.connect()

def wireless_close():
    wireless.close()   
    
def close_sdcard():
    global data_file
    data_file.close()
    
def write_timepoint(current_time, deltaRoll, cumulativeRoll, motor_power):
    global data_file, MOTOR_STILL
    direction = 'STILL'
    print(motor_power)
    if motor_power > MOTOR_STILL:
        direction = 'CCW'
    elif motor_power < MOTOR_STILL:
        direction = 'CW'
    data_file.write(f"{utime.ticks_diff(current_time, LAUNCH_TIME_MS)},{direction},{cumulativeRoll},{deltaRoll},{motor_power}\n")

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
    #inverts accelX (up) and gyroX(roll) - positive is CW
    gyro.set_inv_measures(0b100100)
    time.sleep(0.5)
    #gyro.calibration_test(0, 0)
    
def setup():
    wireless_setup()
    motor_setup()
    gyro_setup()
    sd_card_setup()
    
def closedown():
    wireless_close()
    close_sdcard()
    
def until_launched():
    global gyro, LAUNCH_TIME_MS, LAUNCH_THRESHOLD, APOGEE_UPDATE_TIME
    launch_counter = 0
    while True:
        #if up accel is greater than 2 g's
        if abs(gyro.get_accelX()) > LAUNCH_THRESHOLD:
            launch_counter += 1
            if launch_counter > 2:
                wireless.send("LAUNCHED")
                LAUNCH_TIME_MS = utime.ticks_ms()
                APOGEE_UPDATE_TIME = LAUNCH_TIME_MS
                return True
        time.sleep(0.01)
    #should be unreachable
    return False
    
def get_motor_speed_from_roll(roll):
    return 6 * roll

def update_apogee(delta_time_s):
    global LAUNCH_TIME_MS
    cur_time = utime.ticks_ms()
    if utime.ticks_diff(cur_time, LAUNCH_TIME_MS) / 1000 > 10:
        return False
    return True
    
def send_wireless_dir(motor_speed):
    if motor_speed > 0:
        wireless.send("CW")
    elif motor_speed < 0:
        wireless.send("CCW")

def motor_9090():
    global MOTOR_STILL, LAUNCH_TIME_MS
    cum_roll = 0
    cur_time_ms = utime.ticks_ms()
    while cum_roll < 95:
        prev_time_ms = cur_time_ms
        cur_time_ms = utime.ticks_ms()
        delta_roll = gyro.get_gyro()[0]
        delta_time = utime.ticks_diff(cur_time_ms, prev_time_ms)
        if not update_apogee(delta_time/1000): #past apogee
            break
        cum_roll += delta_roll * delta_time / 1000
        motor_controller.set_speed(1, MOTOR_STILL - 1600) #in case MOTOR_STILL is at 800, ensure we go as fast as possible otherway
        write_timepoint(cur_time_ms, delta_roll, cum_roll, max(MOTOR_STILL - 1600, -800))
        send_wireless_dir(MOTOR_STILL - 1600)
        time.sleep(0.01) #don't overwhelm wireless
    while cum_roll > -5:
        prev_time_ms = cur_time_ms
        cur_time_ms = utime.ticks_ms()
        delta_roll = gyro.get_gyro()[0]
        delta_time = utime.ticks_diff(cur_time_ms, prev_time_ms)
        if not update_apogee(delta_time/1000): #past apogee
            break
        cum_roll += delta_roll * delta_time / 1000
        motor_controller.set_speed(1, MOTOR_STILL + 1600) #in case MOTOR_STILL is at -800, ensure we go as fast as possible otherway
        write_timepoint(cur_time_ms, delta_roll, cum_roll, min(MOTOR_STILL + 1600, 800))
        send_wireless_dir(MOTOR_STILL + 1600)
        time.sleep(0.01) #don't overwhelm wireless
    time.sleep(0.05) #ensure the still command gets through
    motor_controller.set_speed(1, MOTOR_STILL)
    
def motor_stable():
    global gyro, MOTOR_STILL, LAUNCH_TIME_MS
    cum_motor_speed = MOTOR_STILL
    cum_roll = 0
    start_time_ms = utime.ticks_ms()
    cur_time_ms = utime.ticks_ms()
    roll_check = -1
    while True:
        prev_time_ms = cur_time_ms
        cur_time_ms = utime.ticks_ms()
        delta_roll = gyro.get_gyro()[0]
        delta_time = utime.ticks_diff(cur_time_ms, prev_time_ms)
        if not update_apogee(delta_time/1000): #past apogee
            break
        cum_roll += delta_roll * delta_time / 1000
        motor_speed = 0 #so we can record outside of the conditional
        #every 250 milliseconds drive the motor - gives it time to adjust
        if utime.ticks_diff(cur_time_ms, start_time_ms) // 250 > roll_check:
            r_delta_roll = round(delta_roll)
            #print(r_delta_roll)
            roll_check += 1
            cum_motor_speed += get_motor_speed_from_roll(r_delta_roll)
            #fastest direction to go to get back to 0
            min_from_zero = (cum_roll + 180) % 360 - 180
            #print(min_from_zero, r_delta_roll)
            motor_speed = cum_motor_speed + min_from_zero * 5 #return to 0
            motor_controller.set_speed(1, motor_speed)
        send_wireless_dir(motor_speed)
        write_timepoint(cur_time_ms, delta_roll, cum_roll, min(max(motor_speed, -800), 800))
        time.sleep(0.01) #don't overwhelm wireless

setup()
wireless.send("ROLL_CONTROL_READY")
until_launched()
time.sleep(0.25)
motor_9090()
time.sleep(0.1)
motor_stable()
wireless.send("ROLL_END")
closedown()