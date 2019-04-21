from future.utils import raise_

class ActionRegistry(object):
    def __init__(self):
        self.actions = {}
        self.noop_action_name = 'NOOP'

    def register(self, name, description, callback):
        self.actions[self.make_action_name(name)] = {
            'description': description,
            'callback': callback,
        }

    def deregister(self, name):
        self.actions.pop(self.make_action_name(name))

    def make_action_name(self, name):
        return 'ACTION_%s' % name

    def noop(self):
        pass

class RequestReply(object):
    def __init__(self):
        self.handlers = {}

    def set_handler(self, name, description, callback):
        self.handlers[name] = {
            'description': description,
            'callback': callback,
        }

    def unset_handler(self, name):
        self.handlers.pop(name)

    def request(self, name, *args):
        try:
            return self.handlers[name]['callback'](*args)
        except KeyError:
            raise_(KeyError, "No handler '%s' has been set" % name)
