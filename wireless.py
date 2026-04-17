import network
import socket
from time import sleep
import machine
import rp2
import sys
sensor_temp = machine.ADC(4)
rp2.country('US')
ssid = 'BURockets' 
password = 'burockets1' #poor secruity practice but also ¯\_(ツ)_/¯

zero_IP = "192.168.50.1"
zero_Port = 5005
sock = None

def connect():
    global sock
    wlan = network.WLAN(network.STA_IF)

    if wlan.active():
        wlan.active(False)
        sleep(0.5)
        
    wlan.active(True)
    wlan.connect(ssid, password)
    timeout_counter = 15
    while wlan.isconnected() == False and timeout_counter > 0:
        print('Waiting for connection...')
        sleep(1)
        timeout_counter -= 1
    print(wlan.ifconfig())
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return timeout_counter == 0

exception_counter = 0
def send(data):
    global sock, exception_counter
    print(f"attempting to send {data}")
    if sock is None:
        print("no socket")
        return
    try:
       sock.sendto(str(data).encode(),(zero_IP, zero_Port))
       print("sent")
    except Exception as e:
        if exception_counter > 15:
            close()
            exception_counter = 0
            connect()
            
        print(e, exception_counter)
        exception_counter += 1
        return

def close():
    sock.close()