import threading
import time
 
class RelayTimer(object):
    def __init__(self, interval=1, startval=100):
        self.theval = startval
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution
    def run(self):
        """ Method that runs forever """
        while self.theval > 0:
            print self.theval
            self.theval += -1
            time.sleep(self.interval)

spot = 'pond';
timrs={}
timrs[spot]= RelayTimer(1,7)   


 
time.sleep(20)
print('Checkpoint')
timrs['center'] = RelayTimer(5,99)
print("pond time:", timrs['pond'].theval)
print("center time:", timrs['center'].theval)

time.sleep(3)
print('Bye')
print("pond time:",timrs['pond'].theval)
print("center time:", timrs['center'].theval)