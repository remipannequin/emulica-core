import sys
import os.path


def set_path():
#    sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "../emulica-core")))
    sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
