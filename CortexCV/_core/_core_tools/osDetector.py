import sys
from ..._utils import _ANSI

def detectOS():
    if sys.platform.startswith('win'):
        return 'windows'
    elif sys.platform.startswith('darwin'):
        return 'mac'
    elif sys.platform.startswith():
        return 'linux'
    else:
        print(f"{_ANSI.red()}[!] Usupported OS detected. CortexCV does not support your OS yet {_ANSI.reset()}") 