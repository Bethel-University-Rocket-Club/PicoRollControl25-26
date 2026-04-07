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

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    print(wlan.ifconfig())

def send():
    zero_IP = "192.168.50.1"
    zero_Port = 5005
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try: 
        message = "Free me"
        print(message)
        sock.sendto(message.encode(),(zero_IP, zero_Port))
    finally:
        sock.close()


connect()

while (1 == 1):
    send()