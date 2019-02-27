from src.widgets.ui_widgets import *

import tkinter as tk
import os


class StWidget:
    def __init__(s, osi, key, label, col, row, s_type, altkey=None):
        # internal settings key, label for user, column in stframe, row in stframe,
        # type of setting (text, bool, file, folder)
        s.osi = osi
        s.key = key
        s.altkey = altkey
        s.s_type = s_type
        s.mainframe = tk.Frame(s.osi.stframe, bg=COLOR_BUTTON, width=300, height=20, bd=0,
                               highlightbackground=COLOR_BG_3, highlightcolor=COLOR_BG_3, highlightthickness=2)
        s.mainframe.grid(column=col, row=row)
        s.label = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, text=label, font=FONT_M, width=60)
        s.label.grid(column=0, row=0)

        if s_type != "bool":
            s.curlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, text=settings[key], font=FONT_ITALIC,
                                  width=60)
            s.curlabel.grid(column=0, row=1)

        if s_type in ["file", "folder"]:
            s.changebutton = HoverButton(s.mainframe, text="CHANGE", bg=COLOR_BUTTON, width=10, font=FONT_M,
                                         command=lambda: s.osi.st_prompt_setting(key, s_type))
            s.changebutton.grid(column=1, row=0, rowspan=2, sticky="NESW")
            # also verify that this folder/file exists
            if not os.path.exists(settings[key]):
                s.osi.log("WRN: Location not found:")
                s.osi.log("  key>" + key)
                s.osi.log("  val>" + settings[key])

        elif s_type == "bool":
            s.switchbutton = HoverButton(s.mainframe, text=settings[key], bg=COLOR_BUTTON, width=10, font=FONT_M,
                                         command=lambda: s.osi.st_switch_setting(key))
            s.switchbutton.grid(column=1, row=0)

        elif s_type == "list":
            s.nextbutton = HoverButton(s.mainframe, text="SWITCH", bg=COLOR_BUTTON, width=10, font=FONT_M, command=None)
            s.nextbutton.configure(command=lambda: [s.osi.st_cycle_setting(key, altkey)])
            # list should include a method that does something with the setting
            # some setter, for example
            s.nextbutton.grid(column=1, row=0, rowspan=2, sticky="NESW")

        s.mainframe.grid(column=col, row=row, pady=8, padx=8)

    def update(s):
        if s.s_type != "bool":
            s.curlabel.configure(text=settings[s.key])
        else:
            s.switchbutton.configure(text=settings[s.key])
