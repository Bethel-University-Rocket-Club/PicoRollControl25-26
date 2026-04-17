from MPU6050 import MPU6050
from machine import I2C, Pin
import time
import utime

gyro = None

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
    
gyro_setup()
cumAngle = [0,0,0]
prevTime = utime.ticks_ms()
while True:
    deltaAngles = gyro.get_gyro()
    newTime = utime.ticks_ms()
    deltaTime = utime.ticks_diff(newTime, prevTime) * 0.001
    prevTime = newTime
    changeAngle = [a*deltaTime for a in deltaAngles]
    cumAngle = [x+y for x, y in zip(cumAngle, changeAngle)]
    print(f"accel: {gyro.get_accel()}\n gyro: {deltaAngles}\n current angle: {cumAngle}")
    time.sleep(0.01)