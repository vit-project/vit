import glob
import sys
import argparse

from vit import version

parser = argparse.ArgumentParser(
    description="VIT (Visual Interactive Taskwarrior)",
    usage='%(prog)s [options] [report] [filters]',
    formatter_class=argparse.RawTextHelpFormatter,
    allow_abbrev=False,
    epilog="""
VIT (Visual Interactive Taskwarrior) is a lightweight, curses-based front end for
Taskwarrior that provides a convenient way to quickly navigate and process tasks.
VIT allows you to interact with tasks in a Vi-intuitive way.

A goal of VIT is to allow you to customize the way in which you use Taskwarrior's
core commands as well as to provide a framework for easily dispatching external
commands.

While VIT is running, type :help followed by enter to review basic command/navigation actions.

See https://github.com/vit-project/vit for more information.

"""
)

parser.add_argument('-v', '--version',
    action='version',
    version=version.VIT,
)
parser.add_argument('--list-actions',
      dest="list_actions",
      default=False,
      action="store_true",
      help="list all available actions",
)
parser.add_argument('--list-pids',
      dest="list_pids",
      default=False,
      action="store_true",
      help="list all pids found in pid_dir, if configured",
)

def parse_options():
    options, filters = parser.parse_known_args()
    if options.list_actions:
        list_actions()
        sys.exit(0)
    elif options.list_pids:
        ret = list_pids()
        sys.exit(ret)
    return options, filters

def format_dictionary_list(item, description):
    print("%s:" % item)
    print("\t%s\n" % description)

def list_actions():
    from vit.registry import ActionRegistry
    from vit.actions import Actions
    action_registry = ActionRegistry()
    actions = Actions(action_registry)
    actions.register()
    any(format_dictionary_list(action, data['description']) for action, data in actions.get().items())

def _get_pids_from_pid_dir(pid_dir):
        filepaths = glob.glob("%s/*.pid" % pid_dir)
        pids = []
        for filepath in filepaths:
            try:
                with open(filepath, 'r') as f:
                    pids.append(f.read())
            except IOError:
                pass
        return pids

def list_pids():
    from vit.loader import Loader
    from vit.config_parser import ConfigParser
    from vit.pid_manager import PidManager
    loader = Loader()
    config = ConfigParser(loader)
    pid_manager = PidManager(config)
    if pid_manager.pid_dir:
        pids = _get_pids_from_pid_dir(pid_manager.pid_dir)
        print("\n".join(pids))
        return 0
    else:
        print("ERROR: No pid_dir configured")
        return 1
