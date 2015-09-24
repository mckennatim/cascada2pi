
from functools import wraps
from gevent import monkey
from gevent.pywsgi import WSGIServer
monkey.patch_all()
from flask import Flask, render_template, jsonify, request, session, make_response, Response
import datetime
import RPi.GPIO as GPIO
import time
from threading import Timer, Thread
import threading
from flask.ext.cors import CORS
import logging
import json
logging.basicConfig()

print 'dog is Uli'

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'mabibi eats birds'
thread = None

cors = CORS(app)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)



status ={}
status['pond'] = {'spot': 'center', 'state': 'off', 'tleft': 0, 'nexton': 9}
status['center'] = {'spot': 'center', 'state': 'off', 'tleft': 0, 'nexton': 0}
status['bridge'] = {'spot': 'bridge', 'state': 'off', 'tleft': 0, 'nexton': 0}



locs= {'pond':27, 'center': 22, 'bridge':17}
st={'on':1, 'off': 0, 'timer':1}
stof =['off', 'on']
intervalSpeed = 60

class RelayTimer(object):
	gpio =GPIO
	def __init__(self, interval=intervalSpeed, loc='pond'):
		self.loc=loc
		self.port = locs[loc]
		self.interval = interval
		thread = threading.Thread(target=self.run, args=())
		thread.daemon = True                            # Daemonize thread
		thread.start()                                  # Start the exeution
	def run(self):
		""" Method that runs forever """
		print  status[self.loc]
		while 1:
			orig = status[self.loc]['tleft']
			if status[self.loc]['tleft']==0:
				print 'its zero'
				self.gpio.output(self.port, 0)
				status[self.loc]['state']='off'
			if status[self.loc]['tleft']> -1:         
				status[self.loc]['tleft'] =orig -1
				print status[self.loc]['tleft']
			time.sleep(self.interval)



timrs={}
timrs['pond']= RelayTimer(intervalSpeed,'pond')
timrs['center']= RelayTimer(intervalSpeed,'center')
timrs['bridge']= RelayTimer(intervalSpeed,'bridge')

def add_response_headers(headers={}):
    """This decorator adds the headers passed in to the response"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resp = make_response(f(*args, **kwargs))
            h = resp.headers
            for header, value in headers.items():
                h[header] = value
            return resp
        return decorated_function
    return decorator


def cors2(f):
    """This decorator passes X-Robots-Tag: noindex"""
    @wraps(f)
    @add_response_headers({'Access-Control-Allow-Origin': '*'})
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def shutdown_server():
	socketio.server.stop()

def event_stream():
	count = 0
	while True:
		time.sleep(3)
		count += 1
		#data2 = json.dumps({'count': count, 'data':{'pond': {'spot': 'pond', 'tleft': timrs['pond'].tleft, 'state': det_state('pond'),'onoff': stof[GPIO.input(locs['pond'])]}, 'center': {'spot': 'center', 'tleft': timrs['center'].tleft, 'state': det_state('center'),'onoff': stof[GPIO.input(locs['center'])]}, 'bridge': {'spot': 'bridge', 'tleft': timrs['bridge'].tleft, 'state': det_state('bridge'),'onoff': stof[GPIO.input(locs['bridge'])]}}})
		data2 = json.dumps({'count': count, 'data': status})
		#data = timrs['pond'].tleft
		# ssedata= json.dumps({"data": data2, "count": count })
		yield 'data: %s\n\n' % data2

#global thread
if thread is None:
	thread = Thread(target=event_stream)
	thread.start()

def det_state(spot):
	if timrs[spot].tleft > -1:
		return 'timer'
	else: 
		return stof[GPIO.input(locs[spot])]	

def upd_status():
	status['pond']['tleft']= timrs['pond'].tleft
	status['center']['tleft']= timrs['center'].tleft
	status['bridge']['tleft']= timrs['bridge'].tleft

	status['pond']['state'] = det_state('pond')#stof[GPIO.input(locs['pond'])]
	status['bridge']['state'] = det_state('bridge')#stof[GPIO.input(locs['bridge'])]
	status['center']['state'] = det_state('center')#stof[GPIO.input(locs['center'])]
	return status	

@app.route("/")
def hello():
	now = datetime.datetime.now()
	timeString = now.strftime("%Y-%m-%d %H:%M")
	templateData = {
		'title' : 'HELLO!',
		'time': timeString
	}
	return render_template('main2.html', **templateData)

@app.route('/my_event_source')
@cors2
def sse_request():
    return Response(
            event_stream(),
            mimetype='text/event-stream')	

# ctrlWater/?spot=pond&state=on&til=60
@app.route("/ctrlWater/")
def ctrlWater():
	print 'in crtlWater'
	spot = request.args.get('spot')
	state = request.args.get('state')
	til = int(request.args.get('til'))
	print til, spot, state
	# if til:
	# 	timrs[spot]= RelayTimer(60,int(til),locs[spot])   
	# else: #shut down timer
	# 	timrs[spot]= RelayTimer(1,-1,locs[spot]) 

	# if state == 'off' or state =='on':
	# 	timrs[spot]= RelayTimer(1,-1,locs[spot]) 
			 	
	print locs[spot]

	#if state != 'timer':
	GPIO.output(locs[spot], st[state])

	#spot replaces location with  
	status[spot]= {'spot': str(spot), 'tleft':til, 'state':str(state), 'nexton':0}
	print status[spot]


	#return jsonify(spot=spot, state=state, til=til, status=upd_status())
	return jsonify(spot=spot, state=state, til=til, status=status)

@app.route("/report/")
def report():
	return jsonify(spots=status)

@app.route('/shutdown')
def shutdown():
	shutdown_server()
	return 'Server shutting do wn...'   


if __name__ == "__main__":
    http_server = WSGIServer(('0.0.0.0', 8088), app)
    http_server.serve_forever()


