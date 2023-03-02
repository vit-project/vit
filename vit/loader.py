import os
try:
    import importlib.util
except:
    import imp

from vit import env, xdg

DEFAULT_VIT_DIR = '~/.vit'

class Loader:
    def __init__(self):
        self.user_config_dir = os.path.expanduser('VIT_DIR' in env.user and env.user['VIT_DIR'] or DEFAULT_VIT_DIR)

        if not os.path.exists(self.user_config_dir):
            xdg_dir = xdg.get_xdg_config_dir(self.user_config_dir, "vit")
            if xdg_dir:
                self.user_config_dir = xdg_dir

    def load_user_class(self, module_type, module_name, class_name):
        module = '%s.%s' % (module_type, module_name)
        filepath = '%s/%s/%s.py' % (self.user_config_dir, module_type, module_name)
        try:
            mod = self.import_from_path(module, filepath)
        except SyntaxError as e:
            raise SyntaxError("User class: %s (%s) -- %s" % (class_name, filepath, e))
        except:
            return None
        return getattr(mod, class_name)

    def import_from_path(self, module, filepath):
        spec = importlib.util.spec_from_file_location(module, filepath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
