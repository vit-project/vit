from os import path
import sys

PY3 = sys.version_info[0] == 3

DIR = path.dirname(path.abspath(__file__))
VIT = open(path.join(DIR, path.pardir, 'VERSION')).read().strip()
