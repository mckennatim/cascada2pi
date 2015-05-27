from flask import Flask, render_template, jsonify, request
import datetime
import RPi.GPIO as GPIO
import time
from threading import Timer
app = Flask(__name__)

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)
GPIO.setwarnings(False)

status ={}
status['pond'] = {'state': 'off', 'tleft': 0, 'nexton': 0}
status['center'] = {'state': 'off', 'tleft': 0, 'nexton': 0}
status['bridge'] = {'state': 'off', 'tleft': 0, 'nexton': 0}



dict= {'pond':27, 'center': 22, 'bridge':17}
st={'on':1, 'off': 0}

def print_time():
   print "From print_time", time.time()

def print_some_times():
   print time.time()
   Timer(5, print_time, ()).start()
   Timer(10, print_time, ()).start()
   #time.sleep(11)  # sleep while time-delay events execute
   print time.time()  

print_some_times()

@app.route("/")
def hello():
   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M")
   templateData = {
      'title' : 'HELLO!',
      'time': timeString
      }
   return render_template('main.html', **templateData)

@app.route("/readPin/<pin>")
def readPin(pin):
   try:
      GPIO.setup(int(pin), GPIO.IN)
      if GPIO.input(int(pin)) == True:
         response = "Pin number " + pin + " is high!"
      else:
         response = "Pin number " + pin + " is low!"
   except:
      response = "There was an error reading pin " + pin + "."

   templateData = {
      'title' : 'Status of Pin' + pin,
      'response' : response
      }

   return render_template('pin.html', **templateData)

@app.route("/setPin/<pin>")
def setPin(pin):
   try:
      GPIO.output(int(pin), 1)
      response = "Pin number " + pin + " is hi!"
   except:
      response = "There was an error reading pin " + pin + "."

   
   return jsonify(response=response) 

# ctrlWater/?spot=pond$state=on&til=60
@app.route("/ctrlWater/")
def ctrlWater():
   spot = request.args.get('spot')
   state = request.args.get('state')
   til = request.args.get('til')
   print dict[spot]
   GPIO.output(dict[spot], st[state])
   status[spot]= {'tleft':til, 'state':state, 'nexton':0}

   return jsonify(spot=spot, state=state, til=til, status=status)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=True)




