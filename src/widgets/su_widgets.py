from src.utilities import *
from src.widgets.ui_widgets import *

class IpChecker:
    def __init__(s, root, ip, altname=None):
        s.root = root
        s.ip = ip
        s.altname = altname

        s.mainframe = tk.Frame(s.root, bg="pink", height=SU_IP_HEIGHT+5)
        s.indicator = tk.Frame(s.mainframe, height=SU_IP_HEIGHT+5, width=4, bg="green")
        s.indicator.pack(side="left")
        s.iplabel = tk.Label(s.mainframe, fg=COLOR_TEXT, bg=COLOR_BG_2,
                             text="IP: " + (s.altname if s.altname is not None else s.ip))
        s.iplabel.pack(side="left", fill="y")
        s.mainframe.pack(pady=(0,4))