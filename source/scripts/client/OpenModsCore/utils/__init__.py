import BigWorld
from . import events
from .abstract import *
from .analytics import *
from .chat import *
from .game import *
from .iter import *
from .monkeypatch import *


def __import_delayed():
    from . import delayed
    import OpenModsCore
    import sys
    globals()['delayed'] = sys.modules['OpenModsCore.delayed'] = OpenModsCore.delayed = delayed


BigWorld.callback(0, __import_delayed)
del __import_delayed
