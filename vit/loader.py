import os
import importlib.util
from pathlib import Path
from xdg_base_dirs import xdg_config_home


class Loader:

    def __init__(self):
        VIT_CONFIG_FILE = "config.ini"
        # Set the correct vit config file location.
        # VIT searches for the user directory in this order of priority:
        # 1. The VIT_DIR environment variable
        # 2. ~/.vit (the old default location)
        # 3.  A vit directory in any valid XDG base directory (the new default location)
        old_default_vit_config = os.path.join(os.path.expanduser("~/.vit"), VIT_CONFIG_FILE)
        if os.getenv("VIT_DIR"):
            default_vit_dir = os.getenv("VIT_DIR")
            config_path = os.path.join(default_vit_dir, VIT_CONFIG_FILE)
            os.makedirs(default_vit_dir, exist_ok=True)
            self.user_config_file = config_path
        elif os.path.exists(old_default_vit_config):
            self.user_config_file = old_default_vit_config
        else:
            vit_xdg_config_home = os.path.join(xdg_config_home(), 'vit')
            xdg_config_file = os.path.join(vit_xdg_config_home, VIT_CONFIG_FILE)
            os.makedirs(vit_xdg_config_home, exist_ok=True)
            self.user_config_file = xdg_config_file

        self.user_config_dir = os.path.dirname(self.user_config_file)


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
