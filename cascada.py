from flask import Flask, render_template, jsonify, request
import datetime
import RPi.GPIO as GPIO
import time
from threading import Timer
import threading
import time
 
app = Flask(__name__)
app.dbug = False
 
class RelayTimer(object):
   gpio =GPIO
   def __init__(self, interval=1, startval=100, port=27):
      self.port=port
      self.tleft = startval
      self.interval = interval
      thread = threading.Thread(target=self.run, args=())
      thread.daemon = True                            # Daemonize thread
      thread.start()                                  # Start the execution
   def run(self):
      """ Method that runs forever """
      while self.tleft >= 0:
         #print self.tleft
         self.tleft += -1
         if self.tleft==0:
            #print 'its zero'
            self.gpio.output(self.port, 0)         
         time.sleep(self.interval)


GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)
GPIO.setwarnings(False)

status ={}
status['pond'] = {'state': 'off', 'tleft': 0, 'nexton': 0}
status['center'] = {'state': 'off', 'tleft': 0, 'nexton': 0}
status['bridge'] = {'state': 'off', 'tleft': 0, 'nexton': 0}



locs= {'pond':27, 'center': 22, 'bridge':17}
st={'on':1, 'off': 0, 'timer':1}
stof =['off', 'on']

timrs={}
timrs['pond']= RelayTimer(1,-1, locs['pond'])
timrs['center']= RelayTimer(1,-1, locs['center'])
timrs['bridge']= RelayTimer(1,-1, locs['bridge'])


@app.route("/")
def hello():
   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M")
   templateData = {
      'title' : 'HELLO!',
      'time': timeString
      }
   return render_template('main.html', **templateData)

# ctrlWater/?spot=pond&state=on&til=60
@app.route("/ctrlWater/")
def ctrlWater():
   spot = request.args.get('spot')
   state = request.args.get('state')
   til = request.args.get('til')
   print locs[spot]
   timrs[spot]= RelayTimer(60,int(til),locs[spot])   

   GPIO.output(locs[spot], st[state])
   status[spot]= {'tleft':til, 'state':state, 'nexton':0}
   status['pond']['tleft']= timrs['pond'].tleft
   status['center']['tleft']= timrs['center'].tleft
   status['bridge']['tleft']= timrs['bridge'].tleft

   status['pond']['state'] = stof[GPIO.input(locs['pond'])]
   status['bridge']['state'] = stof[GPIO.input(locs['bridge'])]
   status['center']['state'] = stof[GPIO.input(locs['center'])]

   return jsonify(spot=spot, state=state, til=til, status=status)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=True)




