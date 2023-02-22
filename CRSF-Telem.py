import serial # pip install pyserial
import time

com = "COM11"
freq = 62.5
crsf_sync = 0xc8

def crc_init():
    global crc8tab
    crc8tab = [0] * 256
    poly = 0xd5
    crc = 0
    for i in range(0,256):
        crc = i;
        for j in range(0,8):
            crc =(crc << 1) ^ (poly if 0 != (crc & 0x80) else 0);
            #print("j=",j,crc)
        crc8tab[i] = crc & 0xFF
        #print(i,crc8tab[i])

def crc_calc(a):
    crc = 0
    for b in a:
        crc = crc8tab[crc ^ b];
    return crc

def add_crc(a):
    a.append(crc_calc(a))
    a.insert(0,len(a))
    a.insert(0,0xC8)

def ser_init():
    global ser
    ser = serial.Serial(com, 420000)  # open serial port
    print("opened:", ser.name)         # check which port was really used

def ser_tx(a):
    ser.write(bytearray(a))

def crsf_tx(a):
    add_crc(a)
    ser_tx(a)

def hexstr(a):
    s = ""
    for b in a:
         s = s + "{:02X} ".format(b)
    return s

interval = 1.0/freq
t_start = time.time()
ts = t_start - interval
cnt = 0

crc_init()
ser_init()

while True:
    now = time.time()
    if now - ts > interval:
        ts = ts + interval
        cnt = cnt + 1
        i = cnt & 0xff
        #crsf = [0x21, 0x53, 0x54, 0x41, 0x42, 0x00]
        #crsf = [0x80, 0xEA, 0xC8, i, i, i, i,  i,i,i,i,i,i,i,i,i,i,  i,i,i,i,i,i,i,i,i,i]
        crsf = [0x80, 0xEA, 0xC8, i, i, i, i,  i,i,i,i,i,i,i,i,i,i]
        crsf_tx(crsf)
        print("{:d} {:.3f} ".format(cnt, now - t_start) + hexstr(crsf))
ser.close()
