import os

from vit import env


def check_for_existing_xdg_configs(resource):
    xdg_config_home = env.user.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )

    xdg_config_dirs = [xdg_config_home] + (
        env.user.get("XDG_CONFIG_DIRS") or "/etc/xdg"
    ).split(":")

    for config_dir in xdg_config_dirs:
        path = os.path.join(config_dir, resource)
        if os.path.exists(path):
            return path
    return None
