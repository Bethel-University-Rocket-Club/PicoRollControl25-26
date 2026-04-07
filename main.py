from machine import I2C, SPI, Pin
import time
import utime
import os
import motor_control
from MPU6050 import MPU6050
import sdcard
import wireless

gyro = None
sd = None
data_file = None
clockwise = "NEGX" #change this if it the clockwise direction is different

def motor_setup():
    # Configure motor
    motor_control.motor_I2C_bus = I2C(0, scl=Pin(5), sda=Pin(4))
    motor_control.motor_I2C_address = 16
    
    motor_control.init_motor()
    
    motor_control.set_max_acceleration(1, 800)
    motor_control.set_max_deceleration(1, 800)
    
def gyro_setup():
    global gyro
    i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
    gyro = MPU6050(i2c=i2c)
    gyro.reset()
    time.sleep(1)
    gyro._set_defaults()
    gyro.wake()
    gyro._set_power_defaults2(0b111000)
    gyro.set_inv_measures(0b000000)
    time.sleep(0.5)
    #gyro.calibration_test(0, 0)
    
def sdcard_setup():
    global sd, data_file
    spi = SPI(1, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
    sd = sdcard.SDCard(spi, Pin(13))
    # for reading/writing
    vfs = os.VfsFat(sd)
    # where to find the sd card
    os.mount(vfs, '/sd')
    #opening a file in the sdcard
    data_file = open('/sd/data.csv', 'w')
    data_file.write("Time(ms),TurningDirection,currentRoll(CW),deltaRoll(CW)\n")
        
def setup():
    #motor_setup()
    gyro_setup()
    sdcard_setup()
    #done on boot
    #wireless.connect()
    
prevTime = utime.ticks_ms()
def angleChange():
    global gyro, clockwise, prevTime
    newTime = utime.ticks_ms()
    deltaTime = utime.ticks_diff(newTime, prevTime) * 0.001
    prevTime = newTime
    if clockwise == "NEGX":
        return -gyro.get_gyro()[0] * deltaTime
    if clockwise == "X":
        return gyro.get_gyro()[0] * deltaTime
    if clockwise == "NEGY":
        return -gyro.get_gyro()[1] * deltaTime
    if clockwise == "Y":
        return gyro.get_gyro()[1] * deltaTimeMS
    if clockwise == "NEGZ":
        return -gyro.get_gyro()[2] * deltaTimeMS
    if clockwise == "Z":
        return gyro.get_gyro()[2] * deltaTimeMS
    return 0

def write_data(time_from_start, turning_direction, current_angle, angle_change):
    data_file.write(",".join([str(time_from_start), str(turning_direction), str(current_angle), str(angle_change)]) + "\n")

def detect_launch():
    while True:
        time.sleep(2)
    #standard launch?
    #after motor burnout?
    ...
    
def loop():
    global gyro
    cur_angle = 0
    rotDir = "CLOCKWISE"
    speed = 1000
    current_angle_change = 0
    start_time = utime.ticks_ms()
    elapsed_time = start_time
    while True:
        current_angle_change = angleChange()
        elapsed_time = utime.ticks_diff(utime.ticks_ms(), start_time)
        if rotDir == "CLOCKWISE":
            cur_angle += current_angle_change
            write_data(elapsed_time, "CLOCKWISE", cur_angle, current_angle_change)
            if cur_angle >= 110: #begin turning counter-clockwise
                rotDir = "CCLOCKWISE"
            else: #turn clockwise more
                ...
                #set_speed(1, speed)
        elif rotDir == "CCLOCKWISE":
            cur_angle += current_angle_change
            write_data(elapsed_time, "CCLOCKWISE", cur_angle, current_angle_change)
            if cur_angle <= -10: #stop turning
                rotDir = "STOP"
            else: #turn counter-clockwise more
                ...
                #set_speed(1, -speed)
        else: #when rotDir is "STOP"
            break
        wireless.send(rotDir)
        
        
def main():
    #setup()
    detect_launch()
    #loop()
    #data_file.close()

main()