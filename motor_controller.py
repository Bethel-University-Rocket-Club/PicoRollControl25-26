# This example shows a simple way to control the Motoron Motor Controller
# I2C interface using the machine.I2C class in MicroPython, without using
# the Motoron library.

import math
import time
from machine import I2C, Pin

motor_I2C_bus = None
motor_I2C_address = None

def i2c_write(cmd):
  return motor_I2C_bus.writeto(motor_I2C_address, bytes(cmd))
 
def set_max_acceleration(motor, accel):
  i2c_write([
    0x9C, motor, 10, accel & 0x7F, (accel >> 7) & 0x7F,
    0x9C, motor, 12, accel & 0x7F, (accel >> 7) & 0x7F])
 
def set_max_deceleration(motor, decel):
  i2c_write([
    0x9C, motor, 14, decel & 0x7F, (decel >> 7) & 0x7F,
    0x9C, motor, 16, decel & 0x7F, (decel >> 7) & 0x7F])
 
def set_speed(motor, speed):
  #0xD2 is now mode, so it goes to the new speed as fast as possible
  i2c_write([0xD2, motor, speed & 0x7F, (speed >> 7) & 0x7F])

def init_motor():
    i2c_write([
      # Reset the controller to its default settings using a "Reinitialize" command.
      0x96, 0x74,
     
      # Disable CRC using a "Set protocol options" command.
      0x8B, 0x04, 0x7B, 0x43,
     
      # Clear the reset flag using a "Clear latched status flags" command.
      0xA9, 0x00, 0x04,
    ])
    
#default of 1500
def set_timeout_time(time_ms):
    timeout = math.ceil(time_ms / 4)
    i2c_write([0x9C, 0, 5, timeout & 0x7F, (timeout >> 7) & 0x7F])
    