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
   
import RPi.GPIO as GPIO

KAFKA_CONNECT = False

MIN_REFRESH_INTERVAL = 5
LAST_UPDATE = 0
lastUpdateTimestamp = 0

lifx = Lifx(num_bulbs = 1)
@lifx.on_connected
def _connected():
    print "LIFX Connected"

MAXIMUM = 40.0
buffSize = 30

GPIO.setmode(GPIO.BCM)

top = tk.Tk()
top.attributes("-fullscreen", True)
top.configure(background = 'black')


onButton = tk.Button(top, text="on", bg="#001a00", fg='#004d00')
onButton.grid(column = 1, columnspan = 1, row = 0, sticky='nsew')

offButton = tk.Button(top, text="off", bg="#001a00", fg='#004d00')
offButton.grid(column = 0, columnspan = 1, row = 0, sticky='nsew')

sumR = 100
sumG = 100
sumB = 100
def printer(x, y):
   print ('x', x, 'y', y)
   return lambda event:1+2

barHeight = '20'
rCan = tk.Canvas(top, width='255', height=barHeight, relief='raised', bg='black', cursor='dot')
rCan.create_polygon(0, 0, 0, barHeight, sumR, barHeight, sumR, 0, fill = 'red')
rCan.grid(column=0, columnspan=2, row = 2, sticky='w', padx='5')

rCanStrVar = tk.StringVar()
rCanStrVar.set(str(100))
rLabel = tk.Label(top, anchor='center', bd=0, bg='black', cursor='dot', fg='red', textvariable=rCanStrVar)
rLabel.grid(column = 2, row = 2, sticky='w')

gCan = tk.Canvas(top, width='255', height=barHeight, relief='raised', cursor='dot', bg='black')
gCan.create_polygon(0, 0, 0, barHeight, sumG, barHeight, sumG, 0, fill='green')
gCan.grid(column=0, columnspan=2, row = 3, sticky='w', padx='5')
gCan.tag_bind(gCan, "<B1-Motion>", lambda x,y: printer(x, y))
 
gCanStrVar = tk.StringVar()
gCanStrVar.set(str(100))
gLabel = tk.Label(top, anchor='center', bd=0, cursor='dot', bg='black', fg='green', textvariable=gCanStrVar)
gLabel.grid(column = 2, row = 3, sticky='w')

bCan = tk.Canvas(top, width='255', height=barHeight, relief='raised', cursor='dot', bg='black')
bCan.create_polygon(0, 0, 0, barHeight, sumB, barHeight, sumB, 0, fill='blue')
bCan.grid(column=0, columnspan=2, row = 4, sticky='w', padx='5')

bCanStrVar = tk.StringVar()
bCanStrVar.set(str(100))
bLabel = tk.Label(top, anchor='center', bd=0, cursor='dot', fg='blue', bg='black', textvariable=bCanStrVar)
bLabel.grid(column = 2, row = 4, sticky='w')


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
   print 'resend'
   if timer() > LAST_UPDATE + MIN_REFRESH_INTERVAL:
      hsb = RGBtoHSB(float(rCanStrVar.get()), float(gCanStrVar.get()), float(bCanStrVar.get()))
      print('HSB', hsb[0], " ", hsb[1], " ", hsb[2])
      
      lifx.set_light_state(hsb[0], hsb[1], hsb[2], 2700, timeout=2)
      print('updated')
   else:
      print("Timer:", timer(), " prv:", LAST_UPDATE)
   top.update_idletasks()
   top.update()

def updateHeight(can, val, _fill):
   if _fill == 'red':
      rCanStrVar.set(str(val))
   elif _fill == 'green':
      gCanStrVar.set(str(val))
   elif _fill == 'blue':
      bCanStrVar.set(str(val))
   can.create_polygon(0, 0, 0, barHeight, val, barHeight, val, 0, fill=_fill)
   can.create_polygon(val, 0, val, barHeight, 255, barHeight, 255, 0, fill='black')
   resend()
     
#t = threading.Timer(1, resend)
def updateCanvas(fill):
    #if fill == 'red':
    #    rCanStrVar.set(str(event.x))
    #elif fill == 'green':
    #    gCanStrVar.set(str(event.x))
    #elif fill == 'blue':
    #    bCanStrVar.set(str(event.x))
    #t.start()
    return lambda event:updateHeight(event.widget, event.x, fill)

#rCan.bind("<Button-1>", updateCanvas('red'))
rCan.tag_bind(rCan, "<B1-Motion>", lambda x,y:printer( x, y))

#gCan.bind("<Button-1>", updateCanvas('green'))
gCan.tag_bind(gCan, "<Button1-Motion>", lambda x,y:printer(x, y))
bCan.bind("<Button-1>", updateCanvas('blue'))


            
# Main program
lastUpdateTimestamp = timer()
LAST_UPDATE = timer()
if(KAFKA_CONNECT):
   producer = KafkaProducer(bootstrap_servers='128.157.15.203:2181', client_id='R_PI', api_version="0.10")


buffR = queue.Queue()
buffG = queue.Queue()
buffB = queue.Queue()


#for i in range(0, buffSize):
#   _temp = RC_Analog(22)*25
#   buffR.put(_temp)
#   sumR = sumR + _temp

#   _temp = RC_Analog(27)*25
#   buffG.put(_temp)
#   sumG = sumG + _temp

#   _temp = RC_Analog(17)*25
#   buffB.put(_temp)
#   sumB = sumB + _temp


updatemaster = 10
#with lifx.run():
if True:
    #print "INSIDE"
   mTimer = timer()
   with lifx.run():
      top.mainloop()
   #while True:
   #   pass
      #try:
         #analogReadR = (RC_Analog(22)-1)*25
         #sumR-= buffR.get()
         #sumR+= analogReadR
         #buffR.put(analogReadR)
         #buffR.task_done()
         
         #analogReadG = (RC_Analog(27)-1)*25
         #sumG-= buffG.get()
         #sumG+= analogReadG
         #buffG.put(analogReadG)
         #buffG.task_done()
         
         #analogReadB = (RC_Analog(17)-1)*25
         #sumB-= buffB.get()
         #sumB+= analogReadB
         #buffB.put(analogReadB)
         #buffB.task_done()

         #avgR = sumR / float(buffSize)
         #avgG = sumG / float(buffSize)
         #avgB = sumB / float(buffSize)
         
         #updateHeight(rCan, avgR if avgR < 255 else 255, 'red')
         #updateHeight(gCan, avgG if avgG < 255 else 255, 'green')
         #updateHeight(bCan, avgB if avgB < 255 else 255, 'blue')
         #top.update_idletasks()
         #top.update()

         #if timer() - mTimer > updatemaster:
          #  print("Updating light(s)")
           # hsb = RGBtoHSB(min(avgR, 255), min(avgG, 255), min(avgB, 255))
            #lifx.set_light_state(hsb[0], hsb[1], hsb[2], 2400)
            #print "updated"
            #if KAFKA_CONNECT:
              # producer.send('lifx', bytearray(('H'+hsb[0]+'S'+hsb[1]+'B'+hsb[2]), 'utf-8'))
            #mTimer = timer()
            
            #s = str(analogReadR)
            #s = s + " "
            #s = s + str(analogReadG)
            #s = s + " "
            #s = s + str(analogReadB)
            #print s
      #except KeyboardInterrupt:
       #  producer.close()
        # GPIO.cleanup()
