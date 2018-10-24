from src.settings import *

import tkinter as tk
from tkinter import END, LEFT, RIGHT, TOP, BOTTOM, CENTER, RAISED, SUNKEN, X, Y, BOTH, filedialog


class DbLine:  # !!! move to below music classes when done
    def __init__(s, osi, path, indx):
        s.osi = osi
        s.isfile = path.endswith((".txt", ".aegis"))
        s.isaegis = path.endswith(".aegis")
        s.indexval = indx
        # if not s.isfile:
        #     s.indexval = dbstate[2].index(path)
        # else:
        #     if not s.isaegis or not openable: s.indexval = dbstate[1].index(path)+len(dbstate[2])
        #     else:
        #         if openable: s.indexval = dbstate[4].index(display) + len(dbstate[2])

        s.wrapper = tk.Frame(s.osi.dbframe, height=25, bg=COLOR_BG_3)
        s.wrapper.pack_propagate(0)
        s.mainframe = tk.Frame(s.wrapper, bg=COLOR_BUTTON)
        s.indexlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=3,
                                text=('00' + str(s.indexval + 1))[-2:])
        s.indexlabel.pack(side=LEFT, padx=(10, 0))
        s.typelabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=10)
        s.typelabel.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28)
        s.titlelabel.pack(side=LEFT, padx=(10, 0))
        if s.osi.dbstate[3][s.indexval] == "aeg_nokey":
            s.titlelabel.configure(text="-- KEY REQUIRED --")
        elif s.osi.dbstate[3][s.indexval] == "aeg_wrongkey":
            s.titlelabel.configure(text="-- INCORRECT KEY --")
        else:
            s.titlelabel.configure(text=s.osi.dbstate[1][s.indexval])
        #     if s.isfile: s.titlelabel.configure(text=".".join(path.split("\\")[-1].split(".")[:-1]))
        #     else: s.titlelabel.configure(text=path.split("\\")[-1])
        # else: s.titlelabel.configure(text=display)
        if s.isfile:
            if s.isaegis:
                s.typelabel.configure(text="AEGIS")
            else:
                s.typelabel.configure(text="TEXT")
            s.delbutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="DEL", width=6,
                                    relief='ridge', bd=0, activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT,
                                    command=lambda: s.osi.db_interpret("d " + str(s.indexval + 1)))
            s.delbutton.pack(side=RIGHT)
        else:
            s.typelabel.configure(text="FOLDER")
        if s.osi.dbstate[3][s.indexval] not in ["aeg_nokey", "aeg_wrongkey"]:
            s.openbutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="OPEN", width=6,
                                     relief='ridge', bd=0, activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT,
                                     command=lambda: s.osi.db_interpret("o " + str(s.indexval + 1)))
            s.openbutton.pack(side=RIGHT)
        s.mainframe.pack(side=TOP, fill=X, padx=1, pady=1)
        s.wrapper.pack(side=TOP, pady=(2, 0), padx=10, fill=X)
