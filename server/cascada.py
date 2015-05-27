
from gevent import monkey
monkey.patch_all()
from flask import Flask, render_template, jsonify, request, session
import datetime
import RPi.GPIO as GPIO
import time
from threading import Timer, Thread
import threading
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, \
close_room, disconnect
from flask.ext.cors import CORS
import logging
import json
logging.basicConfig()

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'mabibi eats birds'
socketio = SocketIO(app)
thread = None

cors = CORS(app)

class RelayTimer(object):
	gpio =GPIO
	def __init__(self, interval=1, startval=100, port=27):
		self.port=port
		self.tleft = startval
		self.interval = interval
		thread = threading.Thread(target=self.run, args=())
		thread.daemon = True                            # Daemonize thread
		thread.start()                                  # Start the exeution
	def run(self):
		""" Method that runs forever """
		while self.tleft >= 0:
			#print self.tleft
			self.tleft += -1
			if self.tleft==0:
				#print 'its zero'
				self.gpio.output(self.port, 0)         
			time.sleep(self.interval)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)


status ={}
status['pond'] = {'state': 'off', 'tleft': 0, 'nexton': 0}
status['center'] = {'state': 'off', 'tleft': 0, 'nexton': 0}
status['bridge'] = {'state': 'off', 'tleft': 0, 'nexton': 0}



locs= {'pond':27, 'center': 22, 'bridge':17}
st={'on':1, 'off': 0}
stof =['off', 'on']

timrs={}
timrs['pond']= RelayTimer(1,-1, locs['pond'])
timrs['center']= RelayTimer(1,-1, locs['center'])
timrs['bridge']= RelayTimer(1,-1, locs['bridge'])

def shutdown_server():
	socketio.server.stop()

def background_thread():
	"""Example of how to send server generated events to clients."""
	count = 0
	while True:
		time.sleep(4)
		count += 1
		#data2 = jsonify(dog=str(timrs['pond'].tleft) + " my dog has fow")
		#data2 = jsonify(dog=str(123) + " my dog has fow")
		data2 = json.dumps({'pond': {'tleft': timrs['pond'].tleft, 'state': stof[GPIO.input(locs['pond'])]}, 'center': {'tleft': timrs['center'].tleft, 'state': stof[GPIO.input(locs['center'])]}, 'bridge': {'tleft': timrs['bridge'].tleft, 'state': stof[GPIO.input(locs['bridge'])]}})#str(timrs['pond'].tleft) + " my dog has fow"
		data = timrs['pond'].tleft
		#data = 'my dog has fleas'
		print data2
		socketio.emit('my response',
			{'data': data2, 'count': count},
			namespace='/test')    

#global thread
if thread is None:
	thread = Thread(target=background_thread)
	thread.start()

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
	print til
	if til:
		timrs[spot]= RelayTimer(4,int(til),locs[spot])   
	else: #shut down timer
		timrs[spot]= RelayTimer(1,-1,locs[spot])  	
	print locs[spot]

	GPIO.output(locs[spot], st[state])
	status[spot]= {'tleft':til, 'state':state, 'nexton':0}
	status['pond']['tleft']= timrs['pond'].tleft
	status['center']['tleft']= timrs['center'].tleft
	status['bridge']['tleft']= timrs['bridge'].tleft

	status['pond']['state'] = stof[GPIO.input(locs['pond'])]
	status['bridge']['state'] = stof[GPIO.input(locs['bridge'])]
	status['center']['state'] = stof[GPIO.input(locs['center'])]

	return jsonify(spot=spot, state=state, til=til, status=status)

@app.route('/shutdown')
def shutdown():
	shutdown_server()
	return 'Server shutting do wn...'   

@socketio.on('my event', namespace='/test')
def test_message(message):
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my response',
		{'data': message['data'], 'count': session['receive_count']})   

@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my response',
		{'data': message['data'], 'count': session['receive_count']},
		broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
	join_room(message['room'])
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my response',
		{'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
		'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
	leave_room(message['room'])
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my response',
		{'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
		'count': session['receive_count']})


@socketio.on('close room', namespace='/test')
def close(message):
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my response', {'data': 'Room ' + message['room'] + ' is closing.',
		'count': session['receive_count']},
		room=message['room'])
	close_room(message['room'])


@socketio.on('my room event', namespace='/test')
def send_room_message(message):
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my response',
		{'data': message['data'], 'count': session['receive_count']},
		room=message['room'])


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
	session['receive_count'] = session.get('receive_count', 0) + 1
	emit('my response',
		{'data': 'Disconnected!', 'count': session['receive_count']})
	disconnect()          

@socketio.on('connect', namespace='/test')
def test_connect():
	emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
	print('Client disconnected')    


if __name__ == "__main__":
	socketio.run(app, host='0.0.0.0', port=8087)


