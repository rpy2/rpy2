"""This module runs continuous updates for R, such as redrawing graphs when
the plot window is resized. Use the start() and stop() functions to turn
updates on and off.

"""
from rpy2.rinterface import process_revents
import time
import threading


class _EventProcessorThread(threading.Thread):
    """ Call rinterface.process_revents(), pausing 
    for at least EventProcessor.interval between calls. """
    _continue = True

    def run(self):
        while self._continue:
            process_revents()
            time.sleep(EventProcessor.interval)
            
class EventProcessor(object):
    """ Processor for R events (Singleton class) """
    interval = 0.2
    _thread = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance
            
    def start(self):
        """ start the event processor """
        if (self._thread is not None) and (self._thread.is_alive()):
            raise RuntimeException("Processing of R events already started.")
        else:
            self._thread = _EventProcessorThread()
            self._thread.start()

    def stop(self):
        """ stop the event processor """
        self._thread._continue = False
        self._thread.join()
    

def start():
    """ Start the threaded processing of R events. """
    EventProcessor().start()

def stop():
    """ Stop the threaded processing of R events. """
    EventProcessor().stop()

