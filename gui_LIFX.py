import time
import threading
from timeit import default_timer as timer
from lazylights import Lifx
from kafka import KafkaProducer

try:
   import Tkinter as tk
   import Queue as queue
except ImportError:
   import tkinter as tk
   import queue as queue
   
#import RPi.GPIO as GPIO

LIFX_CONNECT = False
KAFKA_CONNECT = True

MIN_REFRESH_INTERVAL = 5
LAST_UPDATE = 0
lastUpdateTimestamp = 0

lifx = Lifx(num_bulbs = 1)
@lifx.on_connected
def _connected():
    print "LIFX Connected"

MAXIMUM = 40.0
buffSize = 30

#GPIO.setmode(GPIO.BCM)

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
   print("R", r, "G", g, "B", b)
   hue = 0
   sat = 0
   bright = 0

   _max = max(r, g, b)/float(255)
   _min = min(r, g, b)/float(255)
   delta = float(_max - _min)
   
   bright = float(_max)
   if _max != 0:
      sat = delta / float(_max)
   else:
      sat = 0
   if sat != 0:
      if r == max(r, g, b):
         hue = float(g/float(255) - b/float(255)) / delta
      elif g == max(r, g, b):
         hue = 2 + (b/float(255) - r/float(255)) / delta
      else:
         hue = 4 + float(r/float(255) - g/float(255)) / delta
   else:
      hue = -1
   hue = hue * 60
   if hue < 0:
      hue+= 360
         
   return (hue, sat, bright)


def resend():
    #if timer() > LAST_UPDATE + MIN_REFRESH_INTERVAL:
      hsb = RGBtoHSB(float(rCanStrVar.get()), float(gCanStrVar.get()), float(bCanStrVar.get()))
      
      print 'HSB', (hsb[0], " ", hsb[1], " ", hsb[2])
      
      if LIFX_CONNECT:
          print("Updating light(s)...")
          lifx.set_light_state(hsb[0], hsb[1], hsb[2], 2400)
                  
      if KAFKA_CONNECT:
          print "Publishing to Kafka..."
          s = 'H'+str(round(hsb[0], 2))+'S'+str(round(hsb[1], 2))+'B'+str(round(hsb[2], 2))
          producer.send('lifx', value=b''.join(s)).get(timeout=5)
              #else:
              #pass
      top.update_idletasks()
      top.update()

def updateHeight(can, val, _fill):
    #Create new bar
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
LAST_UPDATE = timer()

if(KAFKA_CONNECT):
    producer = KafkaProducer(bootstrap_servers='10.101.1.15:9092', client_id='R_PI', api_version="0.10", max_block_ms=4999)


if True:
#with lifx.run():
    top.mainloop()





