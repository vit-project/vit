import uuid

class ActionManagerRegistrar(object):
    def __init__(self, registry):
        self.registry = registry
        self.uuid = uuid.uuid4()

    def register(self, name, callback):
        self.registry.register(self.uuid, name, callback)

    def deregister(self, name=None):
        if name:
            self.registry.deregister(self.uuid, name)
        else:
            any(self.registry.deregister(self.uuid, action) for _, action in self.actions().items())

    def actions(self):
        return self.registry.get_registered(self.uuid)

    def execute_handler(self, *args):
        keys, args = args[0], args[1:]
        handled_action = self.handled_action(keys)
        if handled_action:
            handled_action['callback'](*args)
            data = {
                'name': handled_action['name'],
                'args': args,
            }
            self.registry.event.emit('action-manager:action-executed', data)
            return True
        return False

    def handled_action(self, keys):
        keybindings = self.registry.keybindings
        actions = self.actions()
        if keys in keybindings and 'action_name' in keybindings[keys] and keybindings[keys]['action_name'] in actions:
            return actions[keybindings[keys]['action_name']]
        return None

class ActionManagerRegistry(object):
    def __init__(self, action_registry, keybindings, event=None):
        self.actions = {}
        self.action_registry = action_registry
        self.keybindings = keybindings
        self.event = event

    def get_registrar(self):
        return ActionManagerRegistrar(self)

    def active_registration_id(self, registration_id):
        return registration_id in self.actions

    def get_registered(self, registration_id):
        return self.actions[registration_id] if self.active_registration_id(registration_id) else {}

    def register(self, registration_id, name, callback):
        if not self.active_registration_id(registration_id):
            self.actions[registration_id] = {}
        self.actions[registration_id][self.action_registry.make_action_name(name)] = {
            'name': name,
            'callback': callback,
        }

    def deregister(self, registration_id, name_or_action):
        if self.active_registration_id(registration_id):
            name = name_or_action['name'] if isinstance(name_or_action, dict) else name_or_action
            self.actions[registration_id].pop(self.action_registry.make_action_name(name))

