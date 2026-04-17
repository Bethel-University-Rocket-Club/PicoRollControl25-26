from machine import I2C, SPI, Pin
import time
import utime
import os
import motor_control
from MPU6050 import MPU6050
import sdcard
import wireless

#POSITIVE GYROX IS CLOCKWISE
#NEGATIVE GYROX IS COUNTERCLOCKWISE

gyro = None

sd = None
data_file = None

#2 g's
LAUNCH_THRESHOLD = 2

LAUNCH_TIME_MS = 0

LOOP_SPEED = 0.01

#%3 = 0 is motor 90x90
#%3 = 1 is motor stable
#%3 = 2 is no motor
MODE = 0

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
    
def sd_card_setup():
    global sd, data_file
    spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    sd = sdcard.SDCard(spi, Pin(17))
    # for reading/writing
    vfs = os.VfsFat(sd)
    # where to find the sd card
    os.mount(vfs, '/sd')
    #opening a file in the sdcard
    data_file = open('/sd/data.csv', 'w')
    data_file.write("Time(ms),TurningDirection,currentRoll(CW),deltaRoll(CW)\n")
    
def motor_setup():
    # Configure motor
    motor_control.motor_I2C_bus = I2C(0, scl=Pin(5), sda=Pin(4))
    motor_control.motor_I2C_address = 16
    
    motor_control.init_motor()
    
    motor_control.set_max_acceleration(1, 800)
    motor_control.set_max_deceleration(1, 800)
    
def wireless_setup():
    wireless.connect()
    
def mode_setup():
    global MODE
    MODE = 1
    '''
    with open("config.txt", "r") as f:
        content = f.read()
        try:
            MODE = int(content)
        except Exception as e:
            MODE = 0
            
    #truncates file so its writing to a blank file
    with open("config.txt", "w") as f:
        f.write(str(MODE+1))
        '''
    
def close_sdcard():
    global data_file
    os.umount('/sd')
    data_file.close()
    
    
def write_timepoint(current_time, deltaRoll, cumulativeRoll):
    global data_file
    return
    data_file.write(",".join([time.ticks_diff(current_time, LAUNCH_TIME_MS), "CCW" if deltaRoll > 0 else "CW", cumulativeRoll, deltaRoll]))
        
def wireless_close():
    wireless.close()    
    
def setup():
    wireless_setup()
    gyro_setup()
    motor_setup()
    '''try:
        sd_card_setup()
    except Exception as e:
        wireless.send(str(e))
        '''
    mode_setup()
    
    
def closedown():
    wireless_close()
    #close_sdcard()
    
def until_launched():
    launch_counter = 0
    while True:
        #if up accel is greater than 2 g's
        if gyro.get_accelX() > LAUNCH_THRESHOLD:
            launch_counter += 1
            if launch_counter > 2:
                wireless.send("LAUNCHED")
                LAUNCH_TIME_MS = utime.ticks_ms()
                return True
    #should be unreachable
    return False
    
def until_landed():
    while True:
        motor_control.set_speed(1, 0)
        accel_vals = gyro.get_accel()
        accel_vals = [abs(x) for x in accel_vals]
        still_flags = [x < 1.5 for x in accel_vals]
        if all(still_flags):
            wireless.send("LANDED")
            time.sleep(1.0)
            return True
        
prevTime = utime.ticks_ms()
cumAngle = 0
runningVelocity = 0
runningAltitude = 0
maxAltitude = 0
def motor_9090():
    global prevTime, LAUNCH_TIME_MS, LOOP_SPEED, cumAngle, runningVelocity, runningAltitude, maxAltitude
    overCount = 0
    pastFirst90 = False
    while True:
        if maxAltitude > runningAltitude:
            if overCount > 5:
                break
            overCount += 1
        newTime = utime.ticks_ms()
        deltaTime = LOOP_SPEED
        prevTime = newTime
        deltaRoll = gyro.get_gyroX()
        cumAngle += deltaRoll * deltaTime
        runningVelocity += gyro.get_accelX() * deltaTime
        runningAltitude += runningVelocity * deltaTime
        if maxAltitude < runningAltitude:
            maxAltitude = runningAltitude
        #write_timepoint(newTime, deltaRoll, cumAngle)
        if deltaRoll >= 0:
            wireless.send("ROLL_CW")
        else:
            wireless.send("ROLL_CCW")
        if not pastFirst90:
            if cumAngle > 95:
                pastFirst90 = True
                motor_control.set_speed(1, -800)
            else:
                motor_control.set_speed(1, 800)
        else:
            if cumAngle < -100:
                motor_control.set_speed(1, 0)
                break
            else:
                motor_control.set_speed(1, -800)
        time.sleep(0.01)

                
    wireless.send("ROLL_END")

def motor_stable():
    global prevTime, LAUNCH_TIME_MS, LOOP_SPEED, cumAngle, runningVelocity, runningAltitude, maxAltitude
    prevTime = LAUNCH_TIME_MS
    overCount = 0
    activeRolling = False
    while True:
        if maxAltitude > runningAltitude:
            if overCount > 5:
                break
            overCount += 1
        newTime = utime.ticks_ms()
        deltaTime = LOOP_SPEED
        prevTime = newTime
        deltaRoll = gyro.get_gyroX()
        cumAngle += deltaRoll * deltaTime
        acc = gyro.get_accelX()
        runningVelocity += acc * deltaTime
        runningAltitude += runningVelocity * deltaTime
        if maxAltitude < runningAltitude:
            maxAltitude = runningAltitude
        #print(deltaTime, acc, runningVelocity, maxAltitude, runningAltitude)
        #write_timepoint(newTime, deltaRoll, cumAngle)
        if cumAngle > 10:
            wireless.send("ROLL_CCW")
            motor_control.set_speed(1, -800)
            activeRolling = True
        elif cumAngle < -10:
            wireless.send("ROLL_CW")
            motor_control.set_speed(1, 800)
            activeRolling = True
        else:
            if activeRolling:
                if cumAngle > 2.0:
                    wireless.send("ROLL_CCW")
                    motor_control.set_speed(1, -800)
                elif cumAngle < -2.0:
                    wireless.send("ROLL_CW")
                    motor_control.set_speed(1, 800)
                else:
                    activeRolling = False
            else:
                wireless.send("ROLL_STILL")
                motor_control.set_speed(1, 0)
        time.sleep(0.01)
                
    wireless.send("ROLL_END")
    
#essentially stores data if it can, and returns at apogee
def no_motor():
    global prevTime, LAUNCH_TIME_MS, LOOP_SPEED, cumAngle, runningVelocity, runningAltitude, maxAltitude
    prevTime = LAUNCH_TIME_MS
    overCount = 0
    while True:
        if maxAltitude > runningAltitude:
            if overCount > 5:
                break
            overCount += 1
        newTime = utime.ticks_ms()
        deltaTime = LOOP_SPEED
        prevTime = newTime
        deltaRoll = gyro.get_gyroX()
        cumAngle += deltaRoll * deltaTime
        runningVelocity += gyro.get_accelX() * deltaTime
        runningAltitude += runningVelocity * deltaTime
        if maxAltitude < runningAltitude:
            maxAltitude = runningAltitude
        #write_timepoint(newTime, deltaRoll, cumAngle)
        time.sleep(0.01)
    
def motor_loop():
    global MODE
    print(MODE%3)
    if MODE%3 == 0:
        motor_9090()
    if MODE%3 == 1:
        motor_stable()
    if MODE%3 == 2:
        no_motor()

def main():
    try:
        setup()
        wireless.send("ROLL_CONTROL_READY")
    except Exception as e:
        wireless.send(str(e))
    until_launched()
    motor_loop()
    until_landed()
    closedown()

main()