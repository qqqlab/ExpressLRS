import serial # pip install pyserial
import time

com = "COM11"
tx_freq = 100
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
    
def hexstr2(a):
    s = ""
    for b in a:
        if b == 0xc8: s = s + "\n"
        s = s + "{:02X} ".format(b)
    return s

def crsf_split(a):
    while len(a) >= 4 and a[0] != 0xC8 :
        a = a[1:]
    if len(a) < 4 :
        return a, None
    siz = a[1] + 2
    if len(a) < siz :
        return a, None
    msg = a[:siz]
    return a[siz:], msg


rx_cnt = [0] * 256
rx_bytes = [0] * 256
tx_cnt = 0

tx_interval = 1.0/tx_freq
now = time.time()
t_start = now
tx_ts = now
cnt = 0

crc_init()
ser_init()

ts_stat = now
rx = bytearray()

pkg_len = 10

actual_fc_rx_hz = 0
actual_fc_tx_hz = 0
actual_tx_hz = 0
actual_rx_hz = 0

#receive 
#type 0x80
#0  0xc8
#1 hz //requested FC transmit packet frequency
#2 actual_tx_hz
#3 actual_rx_hz


#transmit CRSF package
#type 0x80
#0 0xEA 
#1 actual_fc_hz //requested FC transmit packet frequency
#2 actual_fc_rx_hz //FC receive rate
#3 actual_fc_tx_hz //FC transmit rate
#4 actual_fc_loop_hz //FC loop rate


while True:
    #statistics
    if time.time() - ts_stat >= 1.0:
        ts_stat = ts_stat + 1.0
        actual_fc_rx_hz = rx_cnt[0x80]
        actual_fc_tx_hz = tx_freq
        print() 
        print("requested: package size:{:d}, rate:{:d} Hz".format(pkg_len,tx_freq))
        for i, val in enumerate(rx_cnt):
            if val > 0 : print ("rx[0x{:02X}]    {:3d} Hz {:5d} B/s".format(i, val, rx_bytes[i]))
        #print ("tx[0x80] {:3d} Hz {:5d} B/s".format(tx_cnt, tx_cnt*pkg_len))
        print ("tx send     {:3d} Hz {:5d} B/s (sent by FC)".format(actual_tx_hz, actual_tx_hz*pkg_len))
        print ("tx received {:3d} Hz {:5d} B/s (received by Radio)".format(actual_rx_hz, actual_rx_hz*pkg_len))
        print ("len:{:2d}  rc:{:3d} Hz  ul/dl:{:3d}/{:3d} Hz  ul/dl:{:4d}/{:4d} B/s".format(pkg_len, rx_cnt[0x16], rx_cnt[0x80], actual_rx_hz, rx_bytes[0x80], actual_rx_hz*pkg_len))
        rx_cnt = [0] * 256
        tx_cnt = 0
        rx_bytes =  [0] * 256

    #transmit
    if time.time() - tx_ts > tx_interval:
        tx_ts = tx_ts + tx_interval
        cnt = cnt + 1
        i = cnt & 0xff
        #crsf = [0x21, 0x53, 0x54, 0x41, 0x42, 0x00]
        #crsf = [0x80, 0xEA, 0xC8, i, i, i, i,  i,i,i,i,i,i,i,i,i,i,  i,i,i,i,i,i,i,i,i,i]
        #crsf = [0x80, 0xEA, 0xC8, i, i, i, i,  i,i,i,i,i,i,i,i,i,i]
        #crsf = [0x80, 0xEA, 0xC8, i, i, i, i] # 10 bytes CRSF
        crsf = [0x80, 0xEA, round(tx_freq), round(actual_fc_rx_hz), round(actual_fc_tx_hz), 0]
        while len(crsf) < pkg_len :
            crsf.append(i)
        crsf_tx(crsf)
        #print("T:{:d} {:.3f} ".format(cnt, time.time() - t_start) + hexstr(crsf))
        tx_cnt = tx_cnt + 1

    #receive
    rx += ser.read(1)
    while True:
        rx, msg = crsf_split(rx)
        if not msg: break
        #print("msg:" + hexstr(msg))
        t = msg[2]
        rx_cnt[t] =  rx_cnt[t] + 1
        rx_bytes[t] = rx_bytes[t] + len(msg)
        if t == 0x80 and msg[3] == 0xC8 :
            tx_freq =  msg[4]
            tx_interval = 1.0/tx_freq
            actual_tx_hz = msg[5]
            actual_rx_hz = msg[6]
            pkg_len = len(msg)
ser.close()
