from src.utilities import *
from src.widgets.ui_widgets import *

import tkinter as tk
from tkinter import LEFT, RIGHT, TOP, X


class PliLine:
    def __init__(s, osi, info):
        s.osi = osi
        s.info = info
        s.plisframe = tk.Frame(s.osi.pliframe, width=260, height=30, bg=COLOR_BG_2)
        s.plisframe.pack_propagate(0)
        s.plitextstring = (s.info[0][6:] + " " * 10)[:10] + " " + (s.info[1] + " " * 3)[:3] + " " + (s.info[2] + " " * 3)[
                                                                                                :3]
        if settings["set_pliduration"] == "True":
            s.plitextstring += " " + (s.info[3] + " " * 5)[:5]
        s.plitext = tk.Label(s.plisframe, font=FONT_M, text=s.plitextstring, bg=COLOR_BG_2, fg=COLOR_TEXT)
        s.plitext.pack(side=LEFT, anchor="w")
        s.pliplaybtn = HoverButton(s.plisframe, font=FONT_M, text="P", bg=COLOR_BG_1, width=2,
                                   command=lambda: s.osi.mp_interpret("pl " + s.info[0][6:]), hover_color="green")
        s.pliloadbtn = HoverButton(s.plisframe, font=FONT_M, text="L", bg=COLOR_BG_1, width=2,
                                   command=lambda: s.osi.mp_interpret("pll " + s.info[0][6:]), hover_color=COLOR_BG_3)
        s.plisavebtn = HoverButton(s.plisframe, font=FONT_M, text="S", bg=COLOR_BG_1, width=2,
                                   command=lambda: s.osi.mp_interpret("plsave " + s.info[0][6:]), hover_color=COLOR_BG_3)
        if s.info[0].startswith("gp pl "):
            s.plisavebtn.configure(state="disabled")
        s.plisavebtn.pack(side=RIGHT, anchor="w")
        s.pliloadbtn.pack(side=RIGHT, anchor="w")
        s.pliplaybtn.pack(side=RIGHT, anchor="w")
        s.plisframe.pack(side=TOP, fill=X, padx=(4, 0))


class MpWidget:
    def __init__(s, osi, path):
        s.osi = osi
        s.path = path
        s.osi.music_paths.append(s.path)
        s.index = s.osi.music_paths.index(s.path)

        # first, getting data from path
        temp = s.path.split("\\")[-3:]
        s.title_name = temp[-1][:-4]
        if is_int(s.title_name.split()[0]):
            s.title_name = " ".join(s.title_name.split()[1:])
        s.artist_name = temp[-3]
        s.album_name = temp[-2]

        # defining single song widget layout
        s.mainframe = tk.Frame(s.osi.mpframe, highlightthickness=0, width=TK_WIDTH - 20, height=28, bd=0)
        s.indexlabel = tk.Label(s.mainframe, font=FONT_M, fg=COLOR_TEXT, width=4, anchor="w",
                                text=(("000" + str(int(s.index) + 1))[-3:]))
        s.indexlabel.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe, font=FONT_M, fg=COLOR_TEXT, width=45, anchor="w", text=s.title_name)
        s.titlelabel.pack(side=LEFT, padx=(0, 10))
        s.artistlabel = tk.Label(s.mainframe, font=FONT_M, fg=COLOR_TEXT, width=25, anchor="w", text=s.artist_name)
        s.artistlabel.pack(side=LEFT, padx=(0, 10))
        s.albumlabel = tk.Label(s.mainframe, font=FONT_M, fg=COLOR_TEXT, width=38, anchor="w", text=s.album_name)
        s.albumlabel.pack(side=LEFT)
        s.buttonframe = tk.Frame(s.mainframe, highlightthickness=0, bd=0, width=60, height=s.mainframe.cget("height")+1)
        s.buttonframe.pack_propagate(0)
        s.destroybutton = tk.Button(s.buttonframe, font=FONT_M, bg=COLOR_BG_3, fg=COLOR_TEXT, command=s.remove,
                                    text="X", width=2, relief="flat")
        s.destroybutton.pack(side=RIGHT, pady=(0, 0))
        s.playbutton = tk.Button(s.buttonframe, font=FONT_M, bg=COLOR_BG_3, fg=COLOR_TEXT,
                                 command=lambda: s.osi.mp_play([s.path]), text="P", width=2, relief="flat")
        s.playbutton.pack(side=RIGHT, padx=(0, 0), pady=(0, 0))
        s.buttonframe.pack(side=RIGHT, pady=(0, 0))

        s.widgetlist = [s.mainframe, s.indexlabel, s.titlelabel, s.artistlabel, s.albumlabel, s.buttonframe]
        s.altlist = [s.destroybutton, s.playbutton]
        if int(s.index % 2 == 0):
            for i in s.widgetlist:
                i.configure(bg=COLOR_BG_2)
            # for i in s.altlist:i.configure(bg=COLOR_BG_1)
        else:
            for i in s.widgetlist:
                i.configure(bg=COLOR_BG_1)
            # for i in s.altlist:i.configure(bg=COLOR_BG_2)

    def show(s):
        s.mainframe.pack(side=TOP, fill=X)

    def hide(s):
        if s.mainframe.winfo_ismapped():
            s.mainframe.pack_forget()

    def update(s):
        temp = str(s.index)[:]
        s.index = s.osi.mp_widgets.index(s)
        if temp != s.index:
            s.indexlabel.configure(text=(("00" + str(int(s.index) + 1))[-2:]))
            if int(s.index % 2 == 0):
                for i in s.widgetlist:
                    i.configure(background=COLOR_BG_2)
            else:
                for i in s.widgetlist:
                    i.configure(background=COLOR_BG_1)

    def remove(s, mass_remove=False):
        # on mass remove, it is assumed that updating tasks will be performed afterwards
        # so s.osi.mp_update_widgets need not be called
        s.update()
        del s.osi.music_paths[s.index]
        s.mainframe.destroy()
        del s.osi.mp_widgets[s.index]
        if not mass_remove:
            s.osi.mp_update_widgets()
