# Angela Kerlin
# CSC 482
# Fall 2021
# Creates a timer that calls the specified function on timeout

import threading

class Timer:

    def __init__(self, time, event):
        self.time = time
        self.event = event
        self.t = None
    
    def start(self):
        # starts the timer
        print(f"Timer started for {self.time} seconds")
        self.t = threading.Timer(self.time, self.event)
        self.t.start()

    def cancel(self):
        # TODO
        if self.t == None:
            # timer wasn't started yet
            return
        self.t.cancel()
