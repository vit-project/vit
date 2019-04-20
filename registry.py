class ActionRegistry(object):
    def __init__(self):
        self.actions = {}

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

