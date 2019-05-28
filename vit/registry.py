import uuid

class ActionRegistrar(object):
    def __init__(self, registry):
        self.registry = registry
        self.uuid = uuid.uuid4()

    def register(self, name, description):
        self.registry.register(self.uuid, name, description)

    def deregister(self, name=None):
        if name:
            self.registry.deregister(name)
        else:
            any(self.registry.deregister(action) for _, action in self.actions().items())

    def actions(self):
        return self.registry.get_registered(self.uuid)

class ActionRegistry(object):
    def __init__(self):
        self.actions = {}
        self.noop_action_name = 'NOOP'

    def get_registrar(self):
        return ActionRegistrar(self)

    def get_registered(self, registration_id):
        return list(filter(lambda action: self.actions[action]['registration_id'] == registration_id, self.actions))

    def register(self, registration_id, name, description):
        self.actions[self.make_action_name(name)] = {
            'name': name,
            'registration_id': registration_id,
            'description': description,
        }

    def deregister(self, name_or_action):
        name = name_or_action['name'] if isinstance(name_or_action, dict) else name_or_action
        self.actions.pop(self.make_action_name(name))

    def get_actions(self):
        return self.actions.keys()

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
            raise KeyError("No handler '%s' has been set" % name)
