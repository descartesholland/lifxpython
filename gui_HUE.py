import time
import threading
from timeit import default_timer as timer
from kafka import KafkaProducer
from phue import Bridge

try:
   import Tkinter as tk
   import Queue as queue
except ImportError:
   import tkinter as tk
   import queue as queue
   
#import RPi.GPIO as GPIO

HUE_CONNECT = False
BRIDGE_IP = '10.101.1.21'
if(HUE_CONNECT):
    bridge = Bridge(BRIDGE_IP)


KAFKA_CONNECT = True
KAFKA_IP = '128.157.15.212:9092'
if(KAFKA_CONNECT):
    producer = KafkaProducer(bootstrap_servers=KAFKA_IP, client_id='R_PI', api_version="0.10", max_block_ms=4999)

MIN_REFRESH_INTERVAL = 2
global lastUpdateTimestamp
global pendingUpdate

#Set up GUI:

top = tk.Tk()
#top.attributes("-fullscreen", True)
top.configure(background = 'black')


onButton = tk.Button(top, text="on", bg="#001a00", fg='#004d00')
onButton.grid(column = 1, columnspan = 1, row = 0, sticky='nsew')

offButton = tk.Button(top, text="off", bg="#001a00", fg='#004d00')
offButton.grid(column = 0, columnspan = 1, row = 0, sticky='nsew')

sumR = 100
sumG = 100
sumB = 100

barHeight = '20'
rCan = tk.Canvas(top, width='255', height=barHeight, relief='raised', bg='black', cursor='dot')
rCanColorPoly = rCan.create_polygon(0, 0, 0, barHeight, sumR, barHeight, sumR, 0, fill = 'red')
rCanBlackPoly = rCan.create_polygon(sumR, 0, sumR, barHeight, 255, barHeight, 255, 0, fill='black')
rCan.itemconfig(rCanColorPoly, tags=('colorPoly'))
rCan.itemconfig(rCanBlackPoly, tags=('blackPoly'))
rCan.grid(column=0, columnspan=2, row = 2, sticky='w', padx='5')

rCanStrVar = tk.StringVar()
rCanStrVar.set(str(100))
rCanLabel = tk.Label(top, anchor='center', bd=0, bg='black', cursor='cross', fg='red', textvariable=rCanStrVar)
rCanLabel.grid(column = 2, row = 2, sticky='w')

gCan = tk.Canvas(top, width='255', height=barHeight, relief='raised', cursor='dot', bg='black')
gCanColorPoly = gCan.create_polygon(0, 0, 0, barHeight, sumG, barHeight, sumG, 0, fill='green')
gCanBlackPoly = gCan.create_polygon(sumG, 0, sumG, barHeight, 255, barHeight, 255, 0, fill='black')
gCan.itemconfig(gCanColorPoly, tags=('colorPoly'))
gCan.itemconfig(gCanBlackPoly, tags=('blackPoly'))
gCan.grid(column=0, columnspan=2, row = 3, sticky='w', padx='5')

gCanStrVar = tk.StringVar()
gCanStrVar.set(str(100))
gCanLabel = tk.Label(top, anchor='center', bd=0, cursor='dot', bg='black', fg='green', textvariable=gCanStrVar)
gCanLabel.grid(column = 2, row = 3, sticky='w')

bCan = tk.Canvas(top, width='255', height=barHeight, relief='raised', cursor='dot', bg='black')
bCanColorPoly = bCan.create_polygon(0, 0, 0, barHeight, sumB, barHeight, sumB, 0, fill='blue')
bCanBlackPoly = bCan.create_polygon(sumB, 0, sumB, barHeight, 255, barHeight, 255, 0, fill='black')
bCan.itemconfig(bCanColorPoly, tags=('colorPoly'))
bCan.itemconfig(bCanBlackPoly, tags=('blackPoly'))
bCan.grid(column=0, columnspan=2, row = 4, sticky='w', padx='5')

bCanStrVar = tk.StringVar()
bCanStrVar.set(str(100))
bCanLabel = tk.Label(top, anchor='center', bd=0, cursor='dot', fg='blue', bg='black', textvariable=bCanStrVar)
bCanLabel.grid(column = 2, row = 4, sticky='w')


top.columnconfigure(0, weight=3)
top.columnconfigure(1, weight=3)
top.columnconfigure(2, weight=1)
top.rowconfigure(0, weight=2)
top.rowconfigure(1, weight=1)
top.rowconfigure(2, weight=1)
top.rowconfigure(3, weight=1)
top.rowconfigure(4, weight=1)


def RGBtoHSB(r, g, b):
#    print("R", r, "G", g, "B", b)
    bright = float(max(r,g,b))
    r = r / float(255)
    g = g / float(255)
    b = b / float(255)
    
    hue = 0
    sat = 0

    _max = max(r, g, b)
    _min = min(r, g, b)
    delta = float(_max - _min)
   
    if delta != 0:
        sat = delta / float(_max)
        del_R = ( ( ( _max - r ) / 6 ) + ( delta / 2 ) ) / delta
        del_G = ( ( ( _max - g ) / 6 ) + ( delta / 2 ) ) / delta
        del_B = ( ( ( _max - b ) / 6 ) + ( delta / 2 ) ) / delta

        if r == _max:
            hue = del_B - del_G
        elif g == _max:
            hue = ( 1 / 3 ) + del_R - del_B
        else:
            hue = ( 2 / 3 ) + del_G - del_R

        if hue < 0:
            hue+= 1
        if hue > 1:
            hue-= 1
         
    return (hue*65535, sat*255, bright)


lastUpdateTimestamp = timer()
pendingUpdate = False

def resend():
    global lastUpdateTimestamp
    global pendingUpdate
    
    if timer() > lastUpdateTimestamp + MIN_REFRESH_INTERVAL:
        pendingUpdate = False
        lastUpdateTimestamp = timer()
        hsb = RGBtoHSB(float(rCanStrVar.get()), float(gCanStrVar.get()), float(bCanStrVar.get()))

        if HUE_CONNECT:
            print("Updating light(s)...")
            for light in bridge.lights:
                light.on = True
                light.hue = int(hsb[0])
                light.saturation = int(hsb[1])
                light.brightness = int(hsb[2])

        if KAFKA_CONNECT:
            print "Publishing to Kafka..."
            s = 'H'+str(round(hsb[0], 2))+'S'+str(round(hsb[1], 2))+'B'+str(round(hsb[2], 2))
            producer.send('hue', value=b''.join(s)).get(timeout=5)

    elif not pendingUpdate:
        pendingUpdate = True
        t = threading.Timer(MIN_REFRESH_INTERVAL, resend)
        t.start()
    top.update_idletasks()
    top.update()

def updateHeight(can, val, _fill):
    can.coords(can.find_withtag("colorPoly"), 0, 0, 0, barHeight, val, barHeight, val, 0)
    can.coords(can.find_withtag("blackPoly"), val, 0, val, barHeight, 255, barHeight, 255, 0)

    top.update_idletasks()
    top.update()
    
    if can == rCan:
        rCanStrVar.set(str(val))
    elif can == gCan:
        gCanStrVar.set(str(val))
    elif can == bCan:
        bCanStrVar.set(str(val))

    hsb = RGBtoHSB(min(int(rCanStrVar.get()), 255), min(int(gCanStrVar.get()), 255), min(int(bCanStrVar.get()), 255))
    
    resend()


#Attach Motion Event Listeners

#rCan.bind("<Button-1>", lambda event:updateHeight(event.widget, event.x, 'red'))
rCan.tag_bind(rCan.find_withtag("colorPoly"), "<B1-Motion>", lambda event:updateHeight(rCan, event.x, 'red'))
rCan.tag_bind(rCan.find_withtag("blackPoly"), "<B1-Motion>", lambda event:updateHeight(rCan, event.x, 'red'))

#gCan.bind("<Button-1>", lambda event:updateHeight(event.widget, event.x, 'green'))
gCan.tag_bind(gCan.find_withtag("colorPoly"), "<B1-Motion>", lambda event:updateHeight(gCan, event.x, 'green'))
gCan.tag_bind(gCan.find_withtag("blackPoly"), "<B1-Motion>", lambda event: updateHeight(gCan, event.x, 'green'))


#bCan.bind("<Button-1>", lambda event:updateHeight(event.widget, event.x, 'blue'))
bCan.tag_bind(bCan.find_withtag("colorPoly"), "<B1-Motion>", lambda event:updateHeight(bCan, event.x, 'blue'))
bCan.tag_bind(bCan.find_withtag("blackPoly"), "<B1-Motion>", lambda event:updateHeight(bCan, event.x, 'blue'))


buffR = queue.Queue()
buffG = queue.Queue()
buffB = queue.Queue()

# Main program
lastUpdateTimestamp = timer()

#if(KAFKA_CONNECT):
#    producer = KafkaProducer(bootstrap_servers='10.101.1.15:9092', client_id='R_PI', api_version="0.10", max_block_ms=4999)

if(HUE_CONNECT):
#    bridge = Bridge(BRIDGE_IP)
#    print "Connecting to Hue bridge..."
    #bridge.connect()

    lights = bridge.lights

if True:
#with lifx.run():
    top.mainloop()





