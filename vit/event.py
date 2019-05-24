# TODO: Use urwid signals instead of custom event emitter?
class Emitter(object):
    """Simple event listener/emitter.
    """
    def __init__(self):
        self.listeners = {}

    def listen(self, event, listener):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(listener)

    def emit(self, event, data=None):
        if event in self.listeners:
            for listener in self.listeners[event]:
                listener(data)
