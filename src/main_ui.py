import glob
import time
from tkinter import filedialog
import subprocess
import os
from random import random
import datetime
from math import ceil

# third party libraries
from mutagen.mp3 import EasyMP3, MP3
from mutagen.id3 import ID3, APIC
from send2trash import send2trash
from Crypto.Cipher import AES

# own classes
from src.file_io import *
from src.widgets.mp_widgets import *
from src.widgets.db_widgets import *
from src.widgets.dl_widgets import *
from src.page_handler import *


# MAIN WINDOW DEFINITION
class MainUI:
    def __init__(s, root, root_directory):
        s.root = root
        s.rootdir = root_directory
        s.DLMAN = None

        # some pre-op (can be anywhere in this init)
        s.pliactive = False
        s.entryhist = ['']
        s.entrypos = 0
        s.state = "max"

        s.mp_page = 0
        s.dl_page = 0

        # global lists for (non)-rendered widgets per tab
        s.mp_widgets = []
        s.db_widgets = []
        s.dl_widgets = []

        s.music_paths = []  # currently selected songs
        s.allfiles = []  # all known songs

        s.db_loc = DB_DIR  # location for database browser
        s.dbstate = ["browse", [], [], []]  # mode, showlist, pathlist, maplist
        s.dbkey = False  # currently entered Aegis key

        s.gppass = settings["gppass"]

        # start of window definition and setup
        root.title("Osiris")
        root.resizable(0, 0)
        s.rootframe = tk.Frame(s.root, background=COLOR_BUTTON)

        s.mainframe = tk.Frame(s.rootframe, bg=COLOR_BUTTON)

        # time for the bulk of the widgets
        s.buttonframe = tk.Frame(s.mainframe, bg=COLOR_BUTTON, height=38)
        s.buttonframe.pack_propagate(0)

        # adding logo
        s.logoframe = tk.Frame(s.buttonframe, height=38, width=80, bg=COLOR_BUTTON)
        s.logoframe.pack_propagate(0)
        s.logoimage = Image.open("etc/background-white-logo.png")
        s.logoimage = s.logoimage.resize((57, 30), Image.ANTIALIAS)
        s.logophoto = ImageTk.PhotoImage(s.logoimage)
        s.logolabel = tk.Label(s.logoframe, height=33, width=66, image=s.logophoto, bg=COLOR_BUTTON)
        s.logolabel.image = s.logophoto
        s.logolabel.pack(padx=10, pady=4)
        s.logoframe.pack(side=LEFT)

        # creating navbar buttons
        s.mpbutton = tk.Button(s.buttonframe, borderwidth=0, activebackground=COLOR_BUTTON_ACTIVE,
                               activeforeground=COLOR_TEXT, font=FONT_L, width=TK_BUTTON_WIDTH, text="MUSIC",
                               command=lambda: s.select("mp"))
        s.dbbutton = tk.Button(s.buttonframe, borderwidth=0, activebackground=COLOR_BUTTON_ACTIVE,
                               activeforeground=COLOR_TEXT, font=FONT_L, width=TK_BUTTON_WIDTH, text="DATABASE",
                               command=lambda: s.select("db"))
        s.dlbutton = tk.Button(s.buttonframe, borderwidth=0, activebackground=COLOR_BUTTON_ACTIVE,
                               activeforeground=COLOR_TEXT, font=FONT_L, width=TK_BUTTON_WIDTH, text="DOWNLOAD",
                               command=lambda: s.select("dl"))
        s.sebutton = tk.Button(s.buttonframe, borderwidth=0, activebackground=COLOR_BUTTON_ACTIVE,
                               activeforeground=COLOR_TEXT, font=FONT_L, width=TK_BUTTON_WIDTH, text="SERVER STATUS",
                               command=lambda: s.select("se"))
        s.stbutton = tk.Button(s.buttonframe, borderwidth=0, activebackground=COLOR_BUTTON_ACTIVE,
                               activeforeground=COLOR_TEXT, font=FONT_L, width=TK_BUTTON_WIDTH, text="SETTINGS",
                               command=lambda: s.select("st"))

        # list of buttons
        s.buttons = [s.mpbutton, s.dbbutton, s.dlbutton, s.sebutton, s.stbutton]

        # pack all buttons
        for i in s.buttons:
            i.pack(side=LEFT, fill=Y)

        # generate window controls if the user opted to omit the Windows navbar
        if settings["set_notitle"] == "True":
            s.exitbutton = tk.Button(s.buttonframe, borderwidth=0, bg=COLOR_BUTTON, activebackground="#c41313",
                                     fg=COLOR_TEXT, activeforeground="white", font=FONT_BOLD, width=4, text=" X ",
                                     command=s.root.destroy)
            s.exitbutton.bind("<Enter>", lambda x: s.exitbutton.configure(bg="#c41313"))
            s.exitbutton.bind("<Leave>", lambda x: s.exitbutton.configure(bg=COLOR_BUTTON))
            s.exitbutton.pack(side=RIGHT, fill=Y)
            # minimize not possible because of overrideredirect
            s.minbutton = tk.Button(s.buttonframe, borderwidth=0, bg=COLOR_BUTTON, activebackground=COLOR_BG_3,
                                    fg=COLOR_TEXT, activeforeground="white", font=FONT_BOLD, width=4, text=" _ ",
                                    command=s.attempt_minimise)
            s.minbutton.bind("<Enter>", lambda x: s.minbutton.configure(bg=COLOR_BG_3))
            s.minbutton.bind("<Leave>", lambda x: s.minbutton.configure(bg=COLOR_BUTTON))
            s.minbutton.pack(side=RIGHT, fill=Y)
        s.buttonframe.grid(column=0, columnspan=2, row=0, sticky="WE")

        # the sandwich goes:
        #  contentwrapperframe
        #   scrollcanvas
        #    contentframe
        #     ALL FRAME WIDGETS (mp, db, dl)
        s.contentwrapperframe = tk.Frame(s.mainframe, bg=COLOR_BG_1, height=TK_HEIGHT - 64, width=TK_WIDTH - 306)
        s.scrollcanvas = tk.Canvas(s.contentwrapperframe, bg=COLOR_BG_1, yscrollincrement="1")
        s.scrollcanvas.pack(side=LEFT, fill=BOTH, expand=True)

        if settings["set_showscrollbar"] == "True":
            s.scrollbar = tk.Scrollbar(s.contentwrapperframe, command=s.scrollcanvas.yview)
            s.scrollbar.pack(side=RIGHT, fill=Y)
            s.scrollcanvas.config(yscrollcommand=s.scrollbar.set)

        s.contentframe = tk.Frame(s.scrollcanvas, bg=COLOR_BG_1)

        if settings["set_scrollable"] == "False":
            s.contentframe.pack(fill=BOTH, expand=True)

        if settings["set_scrollable"] == "True":
            s.scrollcanvas.create_window(0, 0, window=s.contentframe, anchor="nw")
            s.scrollcanvas.bind_all("<MouseWheel>", s.mousewheel)

        s.logoimage = Image.open("etc/osi.png")

        s.mpframe = tk.Frame(s.contentframe, bg=COLOR_BG_1)

        # generate display for currently playing song
        if settings["set_foobarplaying"] == "True":
            s.mpfoobarwrapper = tk.Frame(s.mpframe, bg=COLOR_BUTTON)
            s.mpfoobarwrapper.place(x=1090, y=840, height=100, width=500)

            s.mpfoobarframe = tk.Frame(s.mpfoobarwrapper, bg=COLOR_BG_1)
            s.mpfoobaralbart = tk.Label(s.mpfoobarframe, bg=COLOR_BG_1)
            s.mpfoobaralbart.place(height=100, width=100)

            s.mpfoobar_song = tk.Label(s.mpfoobarframe, text="", width=35, anchor='w', font=FONT_BOLD_M, fg=COLOR_TEXT,
                                       bg=COLOR_BG_1)
            s.mpfoobar_song.place(x=105)
            s.mpfoobar_artist = tk.Label(s.mpfoobarframe, text="", width=35, anchor='w', font=FONT_ITALIC,
                                         fg=COLOR_TEXT, bg=COLOR_BG_1)
            s.mpfoobar_artist.place(x=105, y=30)
            s.mpfoobar_album = tk.Label(s.mpfoobarframe, text="", width=35, anchor='w', font=FONT_ITALIC, fg=COLOR_TEXT,
                                        bg=COLOR_BG_1)
            s.mpfoobar_album.place(x=105, y=60)

            s.mpfoobarplaypause = tk.Label(s.mpfoobarframe, text="", fg=COLOR_TEXT, font=FONT_S, width=10, anchor='e',
                                           bg=COLOR_BG_1)
            if settings["hide_foobarplaying_on_pause"] == "False":
                s.mpfoobarplaypause.place(x=405, y=70)
            s.mpfoobarframe.pack(side=TOP, pady=0, padx=0, fill=BOTH, expand=True)

        s.glbentry = tk.Entry(s.mainframe, font=FONT_L, bg=COLOR_BUTTON, fg=COLOR_TEXT, borderwidth=0,
                              insertbackground=COLOR_TEXT)
        s.glbentry.bind("<Return>", lambda x: s.visentry(s.glbentry.get()))
        s.glbentry.bind("<Up>", lambda x: s.entrymove("up"))
        s.glbentry.bind("<Down>", lambda x: s.entrymove("down"))
        s.glbentry.grid(column=0, row=2, sticky="WE")
        s.glbentry.focus()

        s.dbframe = tk.Frame(s.contentframe, background=COLOR_BG_1)
        s.dbinfoframe = tk.Frame(s.dbframe)
        s.db_loclabel = tk.Label(s.dbinfoframe, bg=COLOR_BG_1, fg=COLOR_TEXT, font=FONT_M, text="Browsing: " + s.db_loc)
        s.db_loclabel.pack(side=LEFT)
        s.dbinfoframe.pack(side=TOP)
        s.dbeditorframe = tk.Frame(s.dbframe, bg=COLOR_BUTTON, highlightthickness=2, highlightbackground=COLOR_BG_3,
                                   highlightcolor=COLOR_BG_3, relief="flat")
        s.dbtitlewrapper = tk.Frame(s.dbeditorframe, bg=COLOR_BG_3)
        s.dbtitle = tk.Text(s.dbtitlewrapper, height=1, bd=0, font=(FONT_M[0], 14), bg=COLOR_BUTTON,
                            insertbackground=COLOR_TEXT, fg=COLOR_TEXT)
        s.dbtitle.pack(fill=X, pady=(0, 2), padx=10)
        s.dbtitlewrapper.pack(fill=X)
        s.dbeditor = tk.Text(s.dbeditorframe, height=TK_LOG_HEIGHT, font=FONT_M, bg=COLOR_BUTTON, bd=0,
                             insertbackground=COLOR_TEXT, fg=COLOR_TEXT, wrap="word")
        s.dbeditor.pack(padx=10, pady=5, fill=BOTH)

        s.dlframe = tk.Frame(s.contentframe, background=COLOR_BG_1)
        s.dlloginreq = tk.Label(s.dlframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=(FONT_M[0], "25"),
                                text="LOGGING IN, PLEASE WAIT")
        s.dlloginreq.pack(side=TOP, fill=BOTH, expand=True, padx=10, pady=10)

        s.seframe = tk.Frame(s.contentframe, background=COLOR_BUTTON)
        s.seframe.grid_propagate(0)

        s.stframe = tk.Frame(s.contentframe, background=COLOR_BG_1)
        # key,label,col,row,type

        # one final thing: the log
        s.logframe = tk.Frame(s.mainframe, width=300, bg=COLOR_BG_1)
        s.loglabel = tk.Label(s.logframe, text="", font=FONT_L, height=TK_LOG_HEIGHT, bg=COLOR_BG_1, fg=COLOR_TEXT,
                              anchor="w", justify=LEFT)  # "SystemButtonFace",text="BAAAAH")
        s.loglabel.pack(pady=(0, 2), fill=X, side=BOTTOM)

        s.logframe.grid(column=1, row=1, sticky="NESW", padx=(6, 0), pady=0)
        s.logframe.pack_propagate(0)

        s.responsiveframe = tk.Frame(s.mainframe, height=26, width=300, bg=COLOR_BUTTON)
        s.responsiveframe.pack_propagate(0)
        s.responsivelabel = tk.Label(s.responsiveframe, text="", height=1, font=FONT_L, bg=COLOR_BUTTON, fg="white")
        s.responsivelabel.pack(side=LEFT)
        s.responsiveframe.grid(column=1, row=2, sticky="e")
        # main window definitions complete, now doing pre-op on the widgets
        # list of modes for convenience

        # lists of things
        s.modes = ["mp", "db", "dl", "se", "st"]
        s.frames = [s.mpframe, s.dbframe, s.dlframe, s.seframe, s.stframe]
        s.interpreters = [s.mp_interpret, s.db_interpret, s.dl_interpret, s.se_interpret, s.st_interpret]

        s.focuslist = [s.dbeditor, s.glbentry]
        # commence the pre-op
        s.contentwrapperframe.grid(column=0, row=1)
        s.contentwrapperframe.pack_propagate(0)

        s.mainframe.grid(column=0, row=0, padx=0, pady=0)

        s.rootframe.pack()

        s.backgroundimage = Image.open("etc/background2.png")
        s.backgroundimage = s.backgroundimage.resize((1000, 1000), Image.ANTIALIAS)
        s.backgroundphoto = ImageTk.PhotoImage(s.backgroundimage)
        s.backgrounds = []
        for i in s.frames:
            s.backgrounds.append(tk.Label(i, image=s.backgroundphoto, bg=COLOR_BG_1))
            s.backgrounds[-1].place(x=-500, y=-500, relx=0.5, rely=0.5)
            s.backgrounds[-1].lower()
        s.select("mp")  # should be the last statement in this init

    # GENERAL DEFS
    def attempt_minimise(s):
        if s.state != "min":
            s.root.geometry("0x0")
            s.state = "forcemin"
            s.root.after(100, s.state_set_min)

    def state_set_min(s):
        s.state = "min"

    def attempt_maximise(s):
        if s.state == "min":
            s.root.geometry(str(TK_WIDTH) + "x" + str(TK_HEIGHT) + "+0+0")
            s.state = "max"

    def entrymove(s, updown):  # handles changing the contents of the entry window
        if s.entrypos == 0:
            s.entryhist[0] = s.glbentry.get()
        if updown == "up" and s.entrypos != len(s.entryhist) - 1:
            s.glbentry.delete("0", len(s.glbentry.get()))
            s.glbentry.insert(END, s.entryhist[s.entrypos + 1])
            s.entrypos += 1
        if updown == "down" and s.entrypos != 0:
            s.glbentry.delete("0", len(s.glbentry.get()))
            s.glbentry.insert(END, s.entryhist[s.entrypos - 1])
            s.entrypos -= 1
        s.responsive()

    def tab_left(s, event):
        s.select(s.modes[s.modes.index(s.mode) - 1])
        return "break"

    def tab_right(s, event):
        s.select(s.modes[(s.modes.index(s.mode) + 1) % (len(s.modes))])
        return "break"

    def mousewheel(s, event):
        s.scrollcanvas.yview_scroll(-1 * int(event.delta / 5), "units")

    def log(s, tolog):
        oldlog = s.loglabel.cget('text')
        newlog = (TK_LOG_HEIGHT * [""] + oldlog.split("\n") + [str(tolog)])[-1 * TK_LOG_HEIGHT:]
        s.loglabel.config(text="\n".join(newlog))

    def greet(s):
        curhour = datetime.datetime.now().hour
        if 5 <= curhour <= 7:
            res = "Up early, sir?"
        elif 7 < curhour < 12:
            res = "Good morning sir"
        elif 12 <= curhour < 18:
            res = "Good afternoon sir"
        elif 18 <= curhour < 24:
            res = "Good evening sir"
        elif curhour < 2:
            res = "Consider sleeping, sir"
        elif curhour < 5:
            res = "Bed. Now."
        else:
            res = "Time has collapsed"

        s.log("OSI: " + res)

    def select(s, choice):
        for i in s.frames:
            i.pack_forget()
        for i in s.buttons:
            i.configure(relief=RAISED, bg=COLOR_BUTTON, fg=COLOR_TEXT)

        # selecting the mode to switch to and applying appropriate widget changes
        s.modeindex = s.modes.index(choice)

        s.buttons[s.modeindex].configure(relief=SUNKEN, bg=COLOR_BUTTON_ACTIVE, fg=COLOR_TEXT)
        s.frames[s.modeindex].pack(fill=BOTH, expand=True, pady=TK_PADDING, padx=TK_PADDING)
        s.mode = choice

    def responsive(s):
        cur = s.glbentry.get()
        msg = ""
        if s.mode == "mp":
            if cur.rstrip(" ") == "":
                msg = ""
            elif cur == "c":
                msg = "Clear all"
            elif cur == "p":
                msg = "Play all"
            elif cur == "rf":
                msg = "Refresh library"
            elif cur == "e":
                msg = "Open foobar"
            elif cur == "pli":
                msg = "Open the playlist screen"
            elif cur == "plic":
                msg = "Close the playlist screen"
            elif cur in ["pl", "pll"]:
                msg = "Please enter a playlist"
            elif cur == "gp":
                msg = "Select most recent GP song"
            elif cur == "bin":
                msg = "Send all to trash"
            elif cur.startswith("plsave "):
                msg = "Save this as a playlist"
            elif cur.startswith(("s ", "p ", "r ", "d ", "bin ", "gp ", "pl ", "pll ")):
                flag = cur.split()[0]
                comm = " ".join(cur.split()[1:])
                if flag == "s":
                    msg = "Select " + str(len(match_criteria(comm, allfiles))) + " song(s)"
                if flag == "p":
                    if s.music_paths == []:
                        msg = "Play " + str(len(match_criteria(comm, allfiles))) + " song(s)"
                    else:
                        msg = "Play " + str(len(match_criteria(comm, s.music_paths))) + " song(s)"
                if flag == "r":
                    msg = "Refine to " + str(len(match_criteria(comm, s.music_paths))) + " song(s)"
                if flag == "d":
                    msg = "Remove " + str(len(match_criteria(comm, s.music_paths))) + " song(s)"
                if flag == "bin":
                    msg = "Send " + str(len(match_criteria(comm, s.music_paths))) + " song(s) to trash"
                if flag == "gp":
                    if is_int(comm):
                        msg = "Select " + comm + " recent song(s)"
                    else:
                        if comm.rstrip(" ") != "":
                            msg = "Is '" + comm + "' a number, dick?"
                if flag == "pl":
                    if read_from_text("mp pl " + comm) is not False:
                        msg = "Play " + str(len(read_from_text("mp pl " + comm))) + " songs"
                    else:
                        msg = "Unknown pl (try 'pli')"
                if flag == "pll":
                    if read_from_text("mp pl " + comm) is not False:
                        msg = "Load " + str(len(read_from_text("mp pl " + comm))) + " songs"
                    else:
                        msg = "Unknown pl (try 'pli')"
            else:
                if s.music_paths == []:
                    msg = "Play " + str(len(match_criteria(cur, allfiles))) + " song(s)"
                else:
                    msg = "Play " + str(len(match_criteria(cur, s.music_paths))) + " song(s)"
        elif s.mode == "gp":
            if cur == "dl":
                msg = "Download this selection"
        s.responsivelabel.config(text=msg)

    def visentry(s, command):
        s.log("USR: " + command)
        s.entryhist = [''] + [command] + s.entryhist[1:]
        s.entrypos = 0
        s.glbentry.delete("0", len(s.glbentry.get()))
        s.responsivelabel.configure(text="")

        s.invisentry(command)

    def invisentry(s, command):  # execute an entry command as normal, but without logging or adding to entry history
        s.interpreters[s.modeindex](command)

    # MUSIC DEFS #######################################################################################################

    def mp_refresh(s):  # refreshes the database index in osData.txt
        '''diskdata = [os.path.join(settings["searchdir"],name)
            for settings["searchdir"], dirs, files in os.walk(settings["searchdir"])
            for name in files
            if name.endswith((".mp3",".flac",".m4a",".wav"))]'''

        diskdata = []
        for ftype in ALLOWED_FILETYPES:
            diskdata.extend(glob.glob(settings["searchdir"] + "**/*" + ftype, recursive=True))

        write_to_text(diskdata, "mp allfiles")
        s.mp_get_files()

    def mp_get_files(s):  # updates allfiles and mp playcount using osData.txt
        global allfiles
        result = read_from_text("mp allfiles")
        if result is not False:
            allfiles = result
        else:
            s.log("OSI: OwO little fucky wucky")
            s.log("OSI: pls restart")
            s.log("OSI: (mp allfiles in osData.txt)")

    def mp_interpret(s, entry):  # interprets the given entry command in the context of the music player
        s.entry = " ".join(entry.split())
        s.cflag = entry.split()[0]
        s.UI = entry[len(s.cflag) + 1:]
        s.oldpaths = s.music_paths[:]
        s.newpaths = s.music_paths[:]

        # start by finding what the new desired paths are
        # also run code that doesn't influence paths, eg: playing, refreshing, saving
        if s.cflag == "s":
            s.newpaths = remove_duplicates(s.oldpaths + match_criteria(s.UI, allfiles))
            s.log("OSI: Added " + str(len(match_criteria(s.UI, allfiles))) + " song(s)")
        elif s.cflag == "r":
            s.newpaths = remove_duplicates(match_criteria(s.UI, s.oldpaths))
            s.log("OSI: Refined to " + str(len(s.newpaths)) + " song(s)")
        elif s.cflag == "d":
            s.newpaths = [x for x in s.oldpaths if x not in match_criteria(s.UI, s.oldpaths)]
            s.log("OSI: Removed " + str(len(s.oldpaths) - len(s.newpaths)) + " song(s)")
        elif s.cflag == "p":
            if s.UI == "" and s.oldpaths != []:
                s.mp_play(s.oldpaths)
            if s.UI != "":
                if s.oldpaths == []:
                    if len(match_criteria(s.UI, allfiles)) != 0:
                        s.mp_play(match_criteria(s.UI, allfiles))
                elif len(match_criteria(s.UI, s.oldpaths)) != 0:
                    s.mp_play(match_criteria(s.UI, s.oldpaths))
        elif s.cflag == "gp":
            s.gpsongs = [x for x in allfiles if "\\GP\\" in x.replace("/", "\\")]
            s.gpsongs.sort(key=lambda x: os.path.getmtime(x))
            if s.UI == "":
                temp = -1
            else:
                temp = -1 * int(s.UI)
            s.newpaths = remove_duplicates(s.gpsongs[temp:] + s.oldpaths)
        elif s.cflag == "bin":
            if s.UI == "":
                for i in s.oldpaths:
                    send2trash(i)
                s.log("OSI: Sent " + str(len(s.oldpaths)) + " song(s) to trash")
                s.newpaths = []
            else:
                for i in remove_duplicates(match_criteria(s.UI, s.oldpaths)):
                    send2trash(i)
                s.newpaths = [x for x in s.oldpaths if x not in match_criteria(s.UI, s.oldpaths)]
                s.log("OSI: Sent " + str(len(s.oldpaths) - len(s.newpaths)) + " song(s) to trash")
            s.mp_refresh()  # also updates local allfiles
        elif s.cflag == "e":
            s.mp_play([])
        elif s.cflag == "c":
            s.newpaths = []
            s.log("OSI: Cleared selection")
        elif s.cflag == "pg":
            if is_int(s.UI):
                s.mp_page = int(s.UI - 1) % ceil(len(s.mp_widgets) / MP_PAGE_SIZE)
        elif s.cflag == "pgn":
            s.mp_page = (s.mp_page + 1) % ceil(len(s.mp_widgets) / MP_PAGE_SIZE)
        elif s.cflag == "pgp":
            s.mp_page = (s.mp_page - 1) % ceil(len(s.mp_widgets) / MP_PAGE_SIZE)
        elif s.cflag == "pl":
            if read_from_text(str("mp pl " + s.UI)) is not False:
                s.mp_play(read_from_text(str("mp pl " + s.UI)))
        elif s.cflag == "plsave":
            if len(s.oldpaths) == 0:
                # logappend("HMP: No song(s) selected")
                pass
            else:
                write_to_text(s.oldpaths, str("mp pl " + s.UI))
                s.log("OSI: Saved playlist")
                try:
                    s.mp_interpret("plic")
                    s.mp_interpret("pli")
                except:
                    pass
        elif s.cflag == "pldel":
            if del_text("mp pl " + s.UI):
                s.log("OSI: Playlist deleted")
            else:
                s.log("ERR: Playlist deletion failed")
        elif s.cflag == "pll":
            if read_from_text(str("mp pl " + s.UI)) is not False:
                s.newpaths = remove_duplicates(s.oldpaths + read_from_text(str("mp pl " + s.UI)))
                s.log("OSI: Loaded " + s.UI)
        elif s.cflag == "rf":
            s.mp_refresh()
            s.log("OSI: Refreshed library")
        elif s.cflag == "pli":  # open the playlist information window
            if not s.pliactive:
                s.mp_generate_pli()
                s.pliactive = True
        elif s.cflag == "plic":  # close the playlist information window
            s.pliwrapper.place_forget()
            s.pliwrapper.destroy()
            s.pliactive = False
        else:
            if s.oldpaths == []:
                if len(match_criteria(s.cflag + " " + s.UI, allfiles)) != 0:
                    s.mp_play(match_criteria(s.cflag + " " + s.UI, allfiles))
            else:
                if len(match_criteria(s.cflag + " " + s.UI, s.oldpaths)) != 0:
                    s.mp_play(match_criteria(s.cflag + " " + s.UI, s.oldpaths))

        for i in range(len(s.newpaths)):
            s.newpaths[i] = "\\".join(s.newpaths[i].split("\\"))
            s.newpaths[i] = "\\".join(s.newpaths[i].split("/"))

        # now that the new paths are known, update the widgets accordingly
        for i in [x for x in s.newpaths if x not in s.oldpaths]:
            s.mp_widgets.append(MpWidget(s, i))

        if len(s.oldpaths) > 0 and len(s.newpaths) == 0:
            s.music_paths = []
            for i in s.mp_widgets:
                i.mainframe.destroy()
            s.mp_widgets = []
        else:
            for i in [x for x in s.oldpaths if x not in s.newpaths]:
                s.mp_widgets[s.music_paths.index(i)].remove(True)  # incredibly inefficient
                s.mp_update_widgets()

        # place any commands that should run after every entry below this line

        # decide which mp_widgets to show
        for i in s.mp_widgets:
            i.hide()
        for i in range((s.mp_page) * MP_PAGE_SIZE, min(len(s.mp_widgets), ((s.mp_page + 1) * MP_PAGE_SIZE))):
            s.mp_widgets[i].show()

        # update page handler
        s.mp_pageHandler.set_page(s.mp_page + 1, len(s.mp_widgets))

        # raise playlist info widget above entries
        try:
            s.pliwrapper.tkraise()
        except:
            pass

    def mp_update_widgets(s):  # get all the MpWidget widgets to update themselves
        for widget in s.mp_widgets:
            widget.update()

    def mp_play(s, songlist):  # function to play a list of .mp3 files with foobar
        # mpcount(songlist)
        s.log("OSI: Playing " + str(len(songlist)) + " song(s)")
        subprocess.Popen([settings["foobarexe"]] + [i for i in songlist], shell=False)

    def mp_generate_pli(s):  # generate the playlist info widget
        # define surrounding layout (regardless of playlists)
        s.pliwrapper = tk.Frame(s.mpframe, bg=COLOR_BUTTON)
        s.pliwrapper.pack_propagate(0)
        s.pliframe = tk.Frame(s.pliwrapper, bg=COLOR_BG_2)
        s.plikeyframe = tk.Frame(s.pliframe, width=260, height=22, bg=COLOR_BG_2)
        s.plikeyframe.pack_propagate(0)
        s.plikeyframe.pack(side=TOP, fill=X, pady=(0, 1))
        s.plitextstring = "Name       #S  #A"
        if settings["set_pliduration"] == "True":
            s.plitextstring += "  Length"
        s.plikey = tk.Label(s.plikeyframe, font=FONT_M, text=s.plitextstring, bg=COLOR_BG_2, fg=COLOR_TEXT)
        s.plikey.pack(side=LEFT, anchor="w")
        s.plikeydel = tk.Button(s.plikeyframe, fg=COLOR_TEXT, font=FONT_M, borderwidth=0, text="X",
                                command=lambda: s.mp_interpret("plic"), bg=COLOR_BUTTON)
        s.plikeydel.pack(side=RIGHT)
        # get all playlists + info
        s.plipllist = []  # 'playlistinfoplaylistlist' i am excellent at naming things
        for i in search_text("mp pl "):
            s.plipllist.append([i[6:]])  # add name
            s.plipllist[-1].append(str(len(read_from_text(i))))  # add number of song(s)
            s.plipllist[-1].append(str(len(remove_duplicates([x.split("/")[-1].split("\\")[1] for x in read_from_text(
                i)]))))  # add number of artists (mildly proud that this worked in one go)
            if settings["set_pliduration"] == "True":
                s.temp_length = sum([int(MP3(x).info.length) for x in read_from_text(i) if '.m4a' not in x])
                s.plipllist[-1].append(str(int(s.temp_length // 60)) + ":" + str(int(s.temp_length % 60)))

        for i in s.plipllist:
            PliLine(i)
        s.pliframe.pack(side=TOP, fill=Y, expand=True)
        s.pliwrapper.place(x=630, width=266, height=TK_HEIGHT)

    # DATABASE DEFS ####################################################################################################
    def db_interpret(s, entry):
        if s.dbstate[0] == "password":
            if not s.dbkey:
                s.dbkey = [entry, ""]
                s.glbentry.delete("0", END)
            elif len(s.dbkey) == 2:
                if s.dbkey[1] == "":
                    s.dbkey[1] = entry
                    s.dbstate[0] = "browse"
                    s.glbentry.delete("0", END)
                    s.glbentry.configure(show="")
                    s.db_refresh()
                    s.glbentry.bind("<Return>", lambda x: s.visentry(s.glbentry.get()))

        # when browsing
        elif s.dbstate[0] == "browse":
            flag = entry.split()[0]
            comm = " ".join(entry.split()[1:])

            if flag == "fulldecrypt" and len(
                    s.dbkey) == 2:  # fully decrypt all files in currect folder, changing only extensions.
                if comm == "affirmative " + s.dbkey[0] + ";" + s.dbkey[1]:
                    # full decrypt confirmed and authorised
                    for i in [x for x in s.dbstate[1] if x.endswith(".aegis")]:
                        reading = open(s.rootdir + s.db_loc + i, "rb")
                        decdata = s.db_aeg_dec(s.dbkey, reading.read(-1))
                        writing = open(s.rootdir + s.db_loc + i + ".txt", "w")
                        writing.write(decdata)
                        reading.close()
                        writing.close()
                        send2trash(s.rootdir + s.db_loc + i)

            elif flag == "fullencrypt" and len(s.dbkey) == 2:
                if comm == "affirmative " + s.dbkey[0] + ";" + s.dbkey[1]:
                    # full encrypt confirmed and authorised
                    for i in [x for x in s.dbstate[1] if x.endswith(".aegis.txt")]:
                        reading = open(s.rootdir + s.db_loc + i, "r")
                        encdata = s.db_aeg_enc(s.dbkey, reading.read(-1))
                        writing = open(s.rootdir + s.db_loc + i.rstrip(".txt"), "wb")
                        writing.write(encdata)
                        reading.close()
                        writing.close()
                        send2trash(s.rootdir + s.db_loc + i)

            elif flag in ["key", "unlock"]:  # decoding keys command
                if comm == "":
                    s.dbkey = False
                    s.dbstate[0] = "password"
                    s.glbentry.configure(show="*")
                    s.glbentry.bind("<Return>", lambda x: s.db_interpret(s.glbentry.get()))
                elif len(comm.split(";")) == 2:
                    s.dbkey = comm.split(";")[:2]
                else:
                    s.log("OSI: Input 2 keys")

            elif flag == "lock":  # delete keys
                s.dbkey = False

            elif flag in ["d", "del", "bin"]:  # delete file / folder
                if comm != "":
                    target = match_criteria(comm, s.dbstate[1])
                    for i in target:
                        targetindex = s.dbstate[1].index(i)
                        i = s.dbstate[2][targetindex]
                        if s.dbstate[3][targetindex] in ["text", "aegis", "folder"]:
                            i = s.db_loc + i
                            send2trash(i)

            elif flag in ["nf", "newf", "nfol", "newfol", "newfolder"]:  # create folder
                if comm not in s.dbstate[2]:
                    os.mkdir(s.db_loc + comm)

            elif flag in ["nt", "newt", "ntxt", "newtxt", "newtext"]:  # create text file
                s.db_switch_state()
                if comm == "":
                    s.db_loc += "*.txt"
                    s.dbtitle.focus_set()
                    s.db_loclabel.configure(text=("Editing: " + s.db_loc))
                else:
                    s.db_loc += comm + ".txt"
                    s.dbtitle.insert("0.0", comm)
                    s.db_loclabel.configure(text=("Editing: " + s.db_loc))

            elif flag in ["na", "newa", "naeg", "newaeg", "newaegis"]:  # create aegis file
                if s.dbkey is not False:
                    s.db_switch_state()
                    if comm == "":
                        s.db_loc += "*.aegis"
                        s.dbtitle.focus_set()
                        s.db_loclabel.configure(text=("Editing: " + s.db_loc))
                    else:
                        s.db_loc += comm + ".aegis"
                        s.dbtitle.insert("0.0", comm)
                        s.db_loclabel.configure(text=("Editing: " + s.db_loc))
                else:
                    s.log("OSI: Key required")

            elif flag in ["u", "up", "b"]:  # go up one or more folders
                if comm == "":
                    comm = 2
                else:
                    comm = int(comm) + 1
                s.db_loc = "/".join(s.db_loc.split("/")[0:max(-1 * (len(s.db_loc.split("/")) - 1), -comm)]) + "/"

            elif flag == "root":  # reset to root
                s.db_loc = DB_DIR

            else:  # open aegis/text/folder
                if flag != "o":
                    comm = flag + " " + comm
                matchresult = match_criteria(comm, s.dbstate[1])
                if matchresult != []:
                    matchresult = matchresult[0]
                    matchindex = s.dbstate[1].index(matchresult)
                    if os.path.isdir(s.rootdir + s.db_loc + matchresult):
                        s.db_loc += match_criteria(comm, s.dbstate[1])[0] + "/"
                    else:
                        if s.dbstate[3][matchindex] == "text":
                            s.dbtitle.insert(END, matchresult)
                            s.db_loc += s.dbstate[2][matchindex]
                            ofile = open(s.rootdir + s.db_loc, "r")
                            lines = ("".join(ofile.readlines())).rstrip("\n")
                            ofile.close()
                            s.db_loclabel.configure(text=("Editing: " + s.db_loc))

                        elif s.dbstate[2][matchindex].endswith(".aegis"):
                            matchpath = s.dbstate[2][matchindex]
                            if s.dbkey is not False:
                                try:
                                    s.db_loc += matchpath
                                    filedata = open(s.rootdir + s.db_loc, "rb")
                                    filedata = s.db_aeg_dec(s.dbkey, filedata.read(-1))
                                    title = filedata.split("\n\n")[0][6:]
                                    lines = "\n\n".join(filedata.split("\n\n")[1:])[5:].rstrip("\n")
                                    s.dbtitle.insert(END, title)
                                    s.db_loclabel.configure(
                                        text=("Editing: " + s.db_loc.rstrip(matchpath) + title + ".aegis"))
                                except:
                                    s.log("OSI: Incorrect key")
                                    return
                            else:
                                s.log("OSI: Key required")
                                return

                        # presuming that file contents have been gotten, switch to edit mode
                        s.db_switch_state()
                        # populate text editor
                        s.dbeditor.insert(END, lines)
                        s.log("OSI: File opened")
                        return

            if s.dbstate[0] == "browse":
                s.db_refresh()

        # when editing
        elif s.dbstate[0] == "edit":
            flag = entry.split()[0]
            try:
                comm = " ".join(entry.split()[1:])
            except:
                pass

            if flag in ["s", "save", "b"]:  # save and exit file

                if s.db_loc.endswith(".txt"):
                    s.db_loc = "/".join(s.db_loc.split("/")[:-1]) + "/" + filter_chars(s.dbtitle.get("0.0", END),
                                                                                   "\\/*<>:?\"|\n") + ".txt"
                    writefile = open(s.rootdir + s.db_loc, "w")
                    writefile.write("\n".join(s.dbeditor.get("0.0", END).split("\n")[:-1]))
                    writefile.close()

                elif s.db_loc.endswith(".aegis"):
                    # assuming key is already entered, else we would not be editing an aegis file
                    if s.dbtitle.get("0.0", END).rstrip("\n") not in [x for x in s.dbstate[1] if
                                                                      s.dbstate[3][s.dbstate[1].index(x)].startswith(
                                                                          "aegis")]:
                        # nonexistant title: new file
                        s.db_loc = "/".join(s.db_loc.split("/")[:-1]) + "/" + str(random()) + ".aegis"
                    writedata = "title:" + s.dbtitle.get("0.0", END).rstrip("\n") + "\n\ndata:"
                    writedata += "\n".join(s.dbeditor.get("0.0", END).split("\n")[:-1])
                    writedata = s.db_aeg_enc(s.dbkey, writedata)
                    writefile = open(s.db_loc, "wb")
                    writefile.write(writedata)
                    writefile.close()
            if flag in ["s", "save", "b", "ns", "nosave"]:
                # clear the editor
                s.dbeditor.delete("0.0", END)
                s.dbtitle.delete("0.0", END)
                s.db_switch_state()
                s.db_loc = "/".join(s.db_loc.split("/")[:-1]) + "/"
                s.db_refresh()

    def db_parse_aeg_key(s, keys, first):
        endkey = ""
        for i in range(32):
            if first:
                endkey += (keys[i % 2] * 32)[i // 2]
            if not first:
                endkey += (keys[(i + 1) % 2][::-1] * 32)[i // 2]
        return str.encode(endkey)

    def db_aeg_enc(s, keys, data):
        data = str.encode(data)
        for i in range(DB_ENC_LEVEL):
            data = s.db_aeg_enc_single(s.db_parse_aeg_key(keys, True), data)

        for i in range(DB_ENC_LEVEL):
            data = s.db_aeg_enc_single(s.db_parse_aeg_key(keys, False), data)

        return data

    def db_aeg_dec(s, keys, data):
        for i in range(DB_ENC_LEVEL):
            data = s.db_aeg_dec_single(s.db_parse_aeg_key(keys, False), data)

        for i in range(DB_ENC_LEVEL):
            data = s.db_aeg_dec_single(s.db_parse_aeg_key(keys, True), data)

        data = data.decode()
        return data

    def db_aeg_enc_single(s, key, data):
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return cipher.nonce + tag + ciphertext

    def db_aeg_dec_single(s, key, data):
        nonce = data[:16]
        tag = data[16:32]
        ciphertext = data[32:]
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        output = cipher.decrypt_and_verify(ciphertext, tag)
        return output

    def db_switch_state(s):
        if s.dbstate[0] == "browse":
            [x.wrapper.destroy() for x in s.db_widgets]
            s.db_widgets = []
            s.dbeditorframe.pack(fill=BOTH)
            s.dbstate[0] = "edit"
        elif s.dbstate[0] == "edit":
            s.dbeditorframe.pack_forget()
            s.dbstate[0] = "browse"

    def db_switch_focus(s, event):
        s.dbeditor.focus_set()
        return "break"

    def db_focus_entry(s, event):
        s.glbentry.focus_set()
        return "break"

    def db_refresh(s):
        # wipe dbstate
        s.dbstate = [s.dbstate[0], [], [], []]
        # wipe current widgets
        [x.wrapper.destroy() for x in s.db_widgets]
        s.db_loclabel.configure(text="Browsing: " + s.db_loc)
        dbtotal = os.listdir(s.rootdir + s.db_loc)
        dbtext = [x for x in dbtotal if x.endswith(".txt")]  # files
        sorted(dbtext, key=str.lower)
        dbaegis = [x for x in dbtotal if x.endswith(".aegis")]
        dbfolders = [x for x in dbtotal if os.path.isdir(s.rootdir + s.db_loc + x)]  # folders
        sorted(dbfolders, key=str.lower)

        # run through folders
        while len(dbfolders) > 0:
            s.dbstate[1].append(dbfolders.pop(0))
            s.dbstate[2].append(s.dbstate[1][-1])
            s.dbstate[3].append("folder")
            s.db_widgets.append(DbLine(s, s.dbstate[1][-1], len(s.dbstate[1]) - 1))

        # run through aegis
        tempshow = []
        temppath = []
        tempmap = []
        while len(dbaegis) > 0:
            if not s.dbkey:
                tempshow.append("")
                temppath.append(dbaegis.pop(0))
                tempmap.append("aeg_nokey")
            else:
                try:
                    filedata = open(s.rootdir + s.db_loc + dbaegis[0], "rb")
                    filedata = s.db_aeg_dec(s.dbkey, filedata.read(-1))
                    title = filedata.split("\n\n")[0][6:]
                    tempshow.append(title)
                    temppath.append(dbaegis.pop(0))
                    tempmap.append("aegis")
                except:
                    tempshow.append("")
                    temppath.append(dbaegis.pop(0))
                    tempmap.append("aeg_wrongkey")
        # after decrypting, sort and add to dbstate
        while len(tempshow) > 0:
            curindex = tempshow.index(min(tempshow))
            s.dbstate[1].append(tempshow.pop(curindex))
            s.dbstate[2].append(temppath.pop(curindex))
            s.dbstate[3].append(tempmap.pop(curindex))
            s.db_widgets.append(DbLine(s, s.dbstate[2][-1], len(s.dbstate[1]) - 1))

        # run through text
        while len(dbtext) > 0:
            s.dbstate[1].append(dbtext.pop(0).rstrip(".txt"))
            s.dbstate[2].append(s.dbstate[1][-1] + ".txt")
            s.dbstate[3].append("text")
            s.db_widgets.append(DbLine(s, s.dbstate[2][-1], len(s.dbstate[1]) - 1))

    # DOWNLOAD DEFS ####################################################################################################

    def dl_interpret(s, entry):
        s.glbentry.delete("0", len(s.glbentry.get()))  # empty the entry field

        if entry.startswith("d ") and is_int(entry.split()[1]):  # if entry is delete command
            # TODO add delete command
            pass

        elif entry.startswith("pg "):
            if is_int(entry[3:]):
                s.dl_page = int(int(entry[3:]) - 1) % ceil(len(s.mp_widgets) / MP_PAGE_SIZE)

        elif entry == "pgn":
            s.dl_page = (s.dl_page + 1) % ceil(len(s.dl_widgets) / DL_PAGE_SIZE)

        elif entry == "pgp":
            s.dl_page = (s.dl_page - 1) % ceil(len(s.dl_widgets) / DL_PAGE_SIZE)

        elif entry == "dl":
            # go through all open widgets and tell them to ready
            for dl in s.dl_widgets:
                dl.ready()
            for dl in s.dl_widgets:
                del s.dl_widgets[s.dl_widgets.index(dl)]
            s.DLMAN.download()

        elif entry.startswith("yt "): # yt single song
            query = "+".join(entry[3:].split())
            res = requests.get(
                "https://www.googleapis.com/youtube/v3/search?part=snippet&q=" + query + "&type=video&key=" + settings[
                    "yt_api_key"])
            data = res.json()["items"][:DL_ALTERNATIVES]
            s.dl_widgets.append(YtSingle([s.yt_get_track_data(x) for x in data]))

        elif entry.startswith(("album ")) and gplogin is not False:
            search_results = s.gpsearch_album(entry[6:])
            if search_results is not False:
                s.dl_widgets.append(GpAlbum(search_results))

        elif entry.startswith(("http://", "https://", "www.", "youtube.com", "play.google")):
            # if true, start parsing URL
            # remove unnecessary prefixes
            urlentry = entry
            for i in ["http://", "https://", "www.", "youtube.com", "play.google", ".com", "/music/"]:
                urlentry = urlentry.split(i)[-1]

            # for GP: note that album ids start with "B" and tracks start with "T"
            url_type = "none"
            url_id = "-"
            if "play.google" in entry and gplogin is not False:
                if urlentry.startswith("m/T"):  # track URL
                    url_id = urlentry[2:].split("?t=")[0]
                    url_type = "gp track"
                if urlentry.startswith("m/B"):  # album URL
                    url_id = urlentry[2:].split("?t=")[0]
                    url_type = "gp album"
                if urlentry.startswith("playlist/"):
                    url_id = urlentry[9:-6] + "=="
                    url_type = "gp playlist"

            elif "youtube" in entry:
                if urlentry.startswith("/playlist?list="):
                    url_id = urlentry[15:]
                    url_type = "yt playlist"
                if urlentry.startswith("/watch?v="):
                    url_id = urlentry[9:]
                    url_type = "yt track"
            else:
                s.log("URL parsing failed")
            s.log("OSI: URL parsed")

            if url_type == "gp track":
                s.dl_widgets.append(GpTrack([s.gp_get_track_data(api.get_track_info(url_id))]))

            if url_type == "gp playlist":
                search_result = api.get_shared_playlist_contents(url_id)
                web_result = webapi.get_shared_playlist_info(url_id)
                pl_info = [
                    filter_(web_result["title"]),
                    filter_(web_result["author"]),
                    str(web_result["num_tracks"]),
                    filter_(web_result["description"]),
                ]
                s.dl_widgets.append(GpPlaylist([s.gp_get_track_data(x["track"]) for x in search_result], pl_info))

            if type == "gp album":
                s.dl_widgets.append(GpAlbum([s.gp_get_album_data(api.get_album_info(url_id, False))]))

            if type == "yt track":
                trackres = requests.get(
                    "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + id + "&key=" + settings[
                        "yt_api_key"])
                s.dl_widgets.append(YtSingle([s.yt_get_track_data(trackres.json()["items"][0])]))

            if type == "yt playlist":
                plres = requests.get(
                    "https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&id=" + url_id + "&key=" +
                    settings["yt_api_key"])
                pldata = plres.json()["items"][0]
                pldata_parsed = [pldata["snippet"]["title"], pldata["snippet"]["channelTitle"],
                                 pldata["contentDetails"]["itemCount"]]

                initial_trackres = requests.get(
                    "https://www.googleapis.com/youtube/v3/"
                    + "playlistItems?part=snippet,contentDetails&maxResults=50&playlistId="
                    + url_id + "&key=" + settings["yt_api_key"])
                initial_trackdata = initial_trackres.json()["items"]
                if pldata_parsed[int(2)] > 50:
                    # if data longer than what can be gotten from 1 request, keep going
                    pagetoken = initial_trackres.json()["nextPageToken"]
                    while 1:
                        next_trackres = requests.get(
                            "https://www.googleapis.com/youtube/v3/"
                            + "playlistItems?part=snippet,contentDetails&maxResults=50&playlistId="
                            + url_id + "&pageToken=" + pagetoken + "&key=" + settings["yt_api_key"])
                        initial_trackdata += next_trackres.json()["items"]
                        try:
                            pagetoken = next_trackres.json()["nextPageToken"]
                        except:
                            break
                s.dl_widgets.append(YtMulti([s.yt_get_track_data(x) for x in initial_trackdata], pldata_parsed))

        elif entry != "" and gplogin is not False:
            # not a command or URL: default behaviour is to search GP for single track
            search_results = s.gpsearch_track(entry)
            if search_results is not False:
                s.dl_widgets.append(GpTrack(search_results))

        # decide which dl widgets to show
        for i in s.dl_widgets:
            i.hide()

        for i in range((s.dl_page) * DL_PAGE_SIZE, min(len(s.dl_widgets), ((s.dl_page + 1) * DL_PAGE_SIZE))):
            s.dl_widgets[i].show()

        # update page handler
        s.dl_pageHandler.set_page(s.dl_page + 1, len(s.dl_widgets))

    def dl_delete(s, object):
        s.dl_widgets.pop(s.dl_widgets.index(object)).wrapper.destroy()

    def db_login_gp(s):
        global Mobileclient, Webclient
        from gmusicapi import Mobileclient, Webclient
        global gplogin
        global api
        global webapi
        api = Mobileclient()
        webapi = Webclient()
        try:
            gptemp = api.login(settings["gpemail"], s.gppass, settings["gpMAC"])
            gptemp2 = webapi.login(settings["gpemail"], s.gppass)
        except Exception as e:
            s.dlloginreq.configure(text="LOGIN FAILED")
            print(e)
            return
        gplogin = gptemp
        s.log("OSI: GP logged in")
        if gplogin:
            s.dlloginreq.pack_forget()
            s.DLMAN.api = api
            s.DLMAN.mainframe.pack(side=BOTTOM, fill=X, pady=(10, 0))
        s.dl_pageHandler = PageHandler(s, "dl", DL_PAGE_SIZE)
        time.sleep(1)
        s.log("OSI: All systems nominal")

    def findborders(s, image):
        bordertop = 0
        borderbottom = 0
        borderleft = 0
        borderright = 0
        imgwidth = image.size[0]
        imgheight = image.size[1]
        for row in range(int(imgheight / 4)):  # look through top quarter of image
            blacks = 0
            for col in range(imgwidth):
                (r, g, b) = image.getpixel((col, row))
                if r + g + b < DL_CROP_THRESH:
                    blacks += 1
            if imgwidth - blacks > 10:  # if row is not primarily black, halt search here
                break
        bordertop = row

        for row in reversed(range(3 * int(imgheight / 4), imgheight)):  # look through bottom quarter of image
            blacks = 0
            for col in range(imgwidth):
                (r, g, b) = image.getpixel((col, row))
                if r + g + b < DL_CROP_THRESH:
                    blacks += 1
            if imgwidth - blacks > 10:  # if row is not primarily black, halt search here
                break
        borderbottom = row

        for col in (range(int(imgwidth / 4))):  # look through left of the image
            blacks = 0
            for row in range(imgheight):
                (r, g, b) = image.getpixel((col, row))
                if r + g + b < DL_CROP_THRESH:
                    blacks += 1
            if imgheight - blacks > 10:  # if row is not primarily black, halt search here
                break
        borderleft = col

        for col in reversed(range(3 * int(imgwidth / 4), imgwidth)):  # look through bottom quarter of image
            blacks = 0
            for row in range(imgheight):
                (r, g, b) = image.getpixel((col, row))
                if r + g + b < DL_CROP_THRESH:
                    blacks += 1
            if imgheight - blacks > 10:  # if row is not primarily black, halt search here
                break
        borderright = col

        return (borderleft, bordertop, borderright, borderbottom)

    def yt_get_track_data(s, track):
        try:
            vid_id = track["contentDetails"]["videoId"]
        except:
            try:
                vid_id = track["id"]["videoId"]
            except:
                vid_id = track["id"]

        return [filter_(str(track["snippet"]["title"])),
                filter_(str(track["snippet"]["channelTitle"])),
                str(track["snippet"]["thumbnails"]["high"]["url"]),
                str(vid_id)]

    def gp_get_track_data(s, track):
        return [filter_(str(track.get("title"))),
                filter_(str(track.get("artist"))),
                filter_(str(track.get("album"))),
                str(track.get("albumArtRef")[0].get("url")),
                filter_(str(track.get("trackNumber"))),
                filter_(str(track.get("storeId"))),
                filter_(str(track.get("composer"))),
                filter_(str(track.get("year"))),
                filter_(str(track.get("beatsPerMinute"))),
                filter_(str(track.get("genre")))]

    def gp_get_album_data(s, album):
        return [filter_(str(album.get("name"))),
                filter_(str(album.get("artist"))),
                filter_(str(album.get("year"))),
                str(album.get("albumArtRef")),
                filter_(str(album.get("albumId"))),
                filter_(str(album.get("explicitType")))]

    def gpsearch_track(s, query):
        # perform search of gp database
        try:
            results = api.search(query).get("song_hits", DL_ALTERNATIVES)[:DL_ALTERNATIVES]
        except IndexError:
            GpLineEmpty(query)
            return False
        curinfo = []
        for i in results:
            i = i.get("track")
            # get relevant results in a list
            curinfo.append(s.gp_get_track_data(i))
            curinfo[-1].append(query)
        return curinfo

    def gpsearch_album(s, query):
        # perform search of gp database
        try:
            results = api.search(query).get("album_hits", DL_ALTERNATIVES)[:DL_ALTERNATIVES]
        except IndexError:
            GpLineEmpty(query)
            return False
        curinfo = []
        for i in results:
            i = i.get("album")
            # get relevant results in a list
            curinfo.append(s.gp_get_album_data(i))
            curinfo[-1].append(query)
        return curinfo

    def dl_url2file(s, url, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # open in binary mode
        with open(filename, "wb") as wfile:
            # get request
            response = requests.get(url)
            # write to file
            wfile.write(response.content)

    def dl_tagify_mp3(s, songpath, tinfo):
        tagfile = EasyMP3(songpath)
        tagfile["title"] = tinfo[0]
        tagfile["artist"] = tinfo[1]
        tagfile["albumartist"] = tinfo[1]
        tagfile["album"] = tinfo[2]
        tagfile["tracknumber"] = ('00' + str(tinfo[4]))[-2:]
        tagfile["composer"] = tinfo[6]
        tagfile["date"] = tinfo[7]
        tagfile["bpm"] = tinfo[8]
        tagfile["genre"] = tinfo[9]
        tagfile.save()

    def dl_albumart_mp3(s, songpath, imagepath):
        audio = MP3(songpath, ID3=ID3)
        try:
            audio.add_tags()
        except:
            pass
        audio.tags.add(APIC(
            encoding=3,  # 3 is for utf-8
            mime='image/png',  # image/jpeg or image/png
            type=3,  # 3 is for the cover image
            desc=u'Cover',
            data=open((imagepath), 'rb').read()))
        audio.save()

    #################################### WORK DEFS #####################################################################

    def se_interpret(s, entry):
        s.log("Under construction")

    #################################### SETTINGS DEFS #####################################################################

    def st_interpret(s, entry):
        pass

    def st_prompt_setting(s, key, type):
        if type == "file":
            newval = tk.filedialog.askopenfilename(initialdir="/".join(settings[key].split("/")[:-1]))
        elif type == "folder":
            newval = tk.filedialog.askdirectory(initialdir="/".join(settings[key].split("/")[:-2])) + "/"
        if newval not in ["", "/"]:
            settings[key] = newval
            s.st_update_settings()

    def st_switch_setting(s, key):
        settings[key] = str(settings[key] == "False")
        s.st_update_settings()

    def st_cycle_setting(s, key,
                         optionskey):  # cycle through a list of options, setting key to the value that comes after the current one
        options = settings[optionskey].split(";")
        current = settings[key]
        if current in options:
            next = options[(options.index(current) + 1) % len(options)]
        else:
            next = options[0]
        settings[key] = next
        s.st_update_settings()

    def st_update_settings(s):
        for i in s.StWidgets: i.update()
        export_settings()
