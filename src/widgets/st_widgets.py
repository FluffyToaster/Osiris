from src.settings import *

import tkinter as tk


class StWidget:
    def __init__(s, osi, key, label, col, row, type,
                 altkey=None):  # internal settings key, label for user, column in stframe, row in stframe, type of setting (text, bool, file, folder)
        s.osi = osi
        s.key = key
        s.altkey = altkey
        s.type = type
        s.mainframe = tk.Frame(s.osi.stframe, bg=COLOR_BUTTON, width=300, height=20, bd=0, highlightbackground=COLOR_BG_3,
                               highlightcolor=COLOR_BG_3, highlightthickness=2)
        s.mainframe.grid(column=col, row=row)
        s.label = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, text=label, font=FONT_M, width=60)
        s.label.grid(column=0, row=0)
        if type != "bool":
            s.curlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, text=settings[key], font=FONT_ITALIC,
                                  width=60)
            s.curlabel.grid(column=0, row=1)
        if type in ["file", "folder"]:
            s.changebutton = tk.Button(s.mainframe, text="CHANGE", bg=COLOR_BUTTON, activeforeground=COLOR_TEXT,
                                       activebackground=COLOR_BG_3, width=10, fg=COLOR_TEXT, border=0, font=FONT_M,
                                       command=lambda: s.osi.st_prompt_setting(key, type))
            s.changebutton.grid(column=1, row=0, rowspan=2, sticky="NESW")
        elif type == "bool":
            s.switchbutton = tk.Button(s.mainframe, text=settings[key], bg=COLOR_BUTTON, width=10,
                                       activeforeground=COLOR_TEXT, activebackground=COLOR_BG_3, fg=COLOR_TEXT,
                                       border=0, font=FONT_M, command=lambda: s.osi.st_switch_setting(key))
            s.switchbutton.grid(column=1, row=0)
        elif type == "list":
            s.nextbutton = tk.Button(s.mainframe, text="SWITCH", bg=COLOR_BUTTON, activeforeground=COLOR_TEXT,
                                     activebackground=COLOR_BG_3, width=10, fg=COLOR_TEXT, border=0, font=FONT_M,
                                     command=None)
            s.nextbutton.configure(command=lambda: [s.osi.st_cycle_setting(key, altkey)])
            # list should include a method that does something with the setting
            # some setter, for example
            s.nextbutton.grid(column=1, row=0, rowspan=2, sticky="NESW")

        s.mainframe.grid(column=col, row=row, pady=8, padx=8)

    def update(s):
        if s.type != "bool":
            s.curlabel.configure(text=settings[s.key])
        else:
            s.switchbutton.configure(text=settings[s.key])
