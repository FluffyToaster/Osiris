# Continuation of the first tkinter shell, nicknamed Osiris
# note that 's.' was used instead of 'self.' because I am an ungodly bastard
# and / or because I am lazy
#
# - RFK 2018 -

# built-in libraries
import time
starting_time = time.time()
def t_since_start(): print(time.time() - starting_time) # call this anywhere to check delays in startup time
import glob
import tkinter as tk
from tkinter import END,LEFT,RIGHT,TOP,BOTTOM,N,E,S,W,NS,CENTER,RAISED,SUNKEN,X,Y,BOTH,filedialog
import subprocess
import os
from random import random
from io import BytesIO
import threading
import datetime
import logging # used to quiet gmusicapi warnings
import queue
from math import ceil, floor

# window fuckery libaries
import tkinter.ttk as ttk
from ctypes import windll

# third party libraries
import requests
from mutagen.mp3 import EasyMP3, MP3
from mutagen.id3 import ID3, APIC
from PIL import Image, ImageTk # use Pillow for python 3.x
from send2trash import send2trash
from Crypto.Cipher import AES

# establishing location and settings
rootdir = os.path.dirname(os.path.realpath(__file__))+"/"
os.chdir(rootdir)
def import_settings(path="etc/settings.txt"):
    global settings
    settings = {}
    settingsfile = open(path,"r")
    for i in settingsfile:
        (key,value) = i.split(" = ")
        value = value.rstrip("\n")
        settings[key] = value
    settingsfile.close()

def export_settings(path="etc/settings.txt"):
    settingsfile = open(path,"w")
    for key,value in settings.items():
        settingsfile.write(key+" = "+value+"\n")
    settingsfile.close()

import_settings()

# LOCAL SETTINGS
# tkinter settings
FONT_S = ("Roboto Mono", "8")  # font name + size
FONT_M = ("Roboto Mono", "10")
FONT_L = ("Roboto Mono", "11")
FONT_ITALIC = ("Roboto Mono", "10", "italic")
FONT_BOLD = ("Roboto Mono", "11", "bold")
FONT_BOLD_M = ("Roboto Mono", "10", "bold")
if settings["large_taskbar"] == "False":
    TK_HEIGHT = 1042
else:
    TK_HEIGHT = 1030
TK_WIDTH = 1920
TK_PADDING = 10
TK_LOG_HEIGHT = 40 # 25 under height 600
TK_BUTTON_WIDTH = 25
TK_PROGRESS_BAR_WIDTH = 1594 # bit arbitrary but should not change in a 1920 width window

# tkinter A E S T H E T I C
COLOR_BG_1 = "#2e3338" # color of general background
COLOR_BG_2 = "#394046" # secondary music selection color
COLOR_BG_3 = "#454d54" # music selection button color
COLOR_BUTTON = "#14161A"
COLOR_BUTTON_ACTIVE = COLOR_BG_1
COLOR_TEXT = "#D3D7DE"

# mp settings
MP_PAGE_SIZE = 32 # widgets rendered on a page
ALLOWED_FILETYPES = [".mp3"] # could also allows ".flac",".m4a",".wav" but would increase time to refresh

# db settings
DB_DIR = "database/"
DB_ENC_LEVEL = 3 # depth of Aegis AES-256 ecryption

# dl settings
DL_PAGE_SIZE = 13 # widgets on a page
DL_ALTERNATIVES = 5 # number of alternatives to display when searching
DL_CROP_THRESH = 50 # used when cropping YT thumbnails

# arguments for subprocess Popen call when downloading from YT
DL_POPEN_ARGS = ['youtube-dl',
                 '-f','bestaudio/best',
                 '-x',
                 '--audio-format','mp3',
                 '--audio-quality','320K']

# setup
mousex, mousey = 0,0 # initialise mouse locations

 # create the database root directory
if not os.path.exists(DB_DIR):
    os.mkdir(DB_DIR)

# global lists for (non)-rendered widgets per tab
mpWidgets = []
dbWidgets = []
dlWidgets = []

musicPaths = [] # currently selected songs
allfiles = [] # all known songs

dbloc = DB_DIR # location for database browser
dbstate = ["browse",[],[],[]] # mode, showlist, pathlist, maplist
dbkey = False # currently entered Aegis key

# make gmusicapi shut up
logging.disable(logging.CRITICAL)

# disgusting windows fuckery to make top bar disappear
GWL_EXSTYLE=-20
WS_EX_APPWINDOW=0x00040000
WS_EX_TOOLWINDOW=0x00000080
def set_appwindow(root): # let the window have a taskbar icon
    hwnd = windll.user32.GetParent(root.winfo_id())
    style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style = style & ~WS_EX_TOOLWINDOW
    style = style | WS_EX_APPWINDOW
    res = windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    root.wm_withdraw()
    root.after(10, lambda: root.wm_deiconify())
# end of windows fuckery


# TOPLEVEL UTILITY FUNCTIONS

# lift the root above other windows and focus on the entry field
def get_attention(root):
    root.lift()
    root.attributes("-topmost", True)
    root.attributes("-topmost", False)
    root.after(10,lambda: set_appwindow(root))
    root.after(200,lambda: root.focus_force())
    root.after(300,lambda: OSI.glbentry.focus())

# adjust recorded mouse location according to event
def def_delta(event):
    global mousex, mousey
    mousex = event.x
    mousey = event.y

# move the window with the mouse
def move_window(event):
    if settings["set_draggable"] == "True":
        root.geometry("+"+str(event.x_root-mousex)+"+"+str(event.y_root-mousey))

# often-used search function: uses the given criteria to filter the total list
# param find - a string, built from ';'-separated filter commands
# param total - an array of strings, each string is evaluated separately
def search(find,total):
    # find can be read as written in DNF, with the OR's as ';'
    find = find.split(";")
    results = []
    for term in find: # each term is evaluated over the total
        term = term.split()
        remlist = []
        for single in term:
            if single.startswith("-"):
                remlist.append(single[1:])
        for full in total: # loops through every entry in the total list
            match = True
            for single in term:
                if not single.startswith("-"):
                    if single.lower() not in full.lower(): match = False
            if match:
                for rem in remlist:
                    if rem.lower() in full.lower(): match = False
                if match and full not in results:
                    results.append(full)
    return results

# interpret search criteria and returns matches
def match_criteria(crit, searchlist):
    match = [] #list of all files that match criteria given
    for i in crit.split(";"):
        if len(i.split("-"))==2:
            if is_int(i.split("-")[0]) and is_int(i.split("-")[1]):
                # criterium is range of files
                match += searchlist[int(i.split("-")[0])-1:int(i.split("-")[1])]
        if is_int(i):
            # criterium is single file
            if int(i) <= len(searchlist):
                match += [searchlist[int(i)-1]]
        else:
            # criterium is string to search
            match += search(i,searchlist)
    return match

# check whether a value can be converted to an integer
def is_int(val):
    try:
        int(val)
        return True
    except:
        return False

# remove duplicate values from a list
def remove_duplicates(duplist):
    seen = set()
    seen_add = seen.add
    return [x for x in duplist if not (x in seen or seen_add(x))]

# filter characters from a string
def filter_chars(string_in,chars):
    out = "".join(list(filter(lambda x: x not in chars, list(string_in))))
    return out

# escape backslashes
def escape(string):
    val = repr(string)
    for i in range(4):
        val = val.replace([r"\x0",r"\n",r"\l",r"\t"][i],
                          [r"\\0",r"\\n",r"\\l",r"\\t"][i])
    return val.strip("'")

# handle unsafe strings, make them UTF-8 compliant
def filter_(orig_string, make_safe_for_filename = True):
    temp = orig_string[:]
    if make_safe_for_filename:
        changelist = '*/\\":?<>|'
        for char in changelist:
            temp = "_".join(temp.split(char))

    return bytes(temp, 'utf-8').decode('utf-8','replace')

# get the most frequent color from an image
def color_from_image(image, avoid_dark = False):
    colors = image.getcolors(image.size[0]*image.size[1])
    max_occurence, most_present = 0, 0
    for c in colors:
        if c[0] > max_occurence and (not(avoid_dark) or sum(c[1]) > 100):
            (max_occurence, most_present) = c
    return most_present

# parse an RGB tuple into a Hex color string
def RGBToHex(rgb):
    return ("#"+('00'+str(hex(rgb[0]))[2:])[-2:]+('00'+str(hex(rgb[1]))[2:])[-2:]+('00'+str(hex(rgb[2]))[2:])[-2:])


# TOPLEVEL TEXT INTERACTION DEFS
# get the content of osData.txt, also applicable for other .txt files
def select_file(filepath=settings["datapath"]):
    with open(filepath,"r",encoding="utf-8") as selectedFile:
        data = [x.strip('\n') for x in selectedFile.readlines()]
    return data

# replace the current content of section with that of writelist, creates section if there is none
def write_to_text(writelist,section):
    data = select_file()
    try:
        start = data.index("="+section+"=")+1
        end = data.index("=/"+section+"=")
    except:
        data += ["="+section+"="] + "\n" + ["=/"+section+"="]
        start = data.index("="+section+"=")+1
        end = data.index("=/"+section+"=")
    data[start:end] = []
    for i in writelist[::-1]:
        data.insert(start,i)
    write_file = open(settings["datapath"],"w",encoding="utf-8")
    for i in data:
        write_file.write(i+"\n")
    write_file.close()

# gets the content of a section
def read_from_text(section):
    data = select_file()
    try:
        start = data.index("="+section+"=")+1
        end = data.index("=/"+section+"=")
    except: return False
    return(data[start:end])

def del_text(section): # deletes a section
    data = select_file()
    try: data[(data.index("="+section+"=")):(data.index("=/"+section+"=")+1)] = []
    except: return False
    write_file = open(settings["datapath"],"w",encoding="utf-8")
    for i in data: write_file.write(i+"\n")
    write_file.close()
    return True

def search_text(section): # returns the names of all matching sections
    data = select_file()
    result = search(str("="+section),data)
    if result != False:
        for i in range(len(result)): result[i] = result[i][1:-1]
    return result

# TOP LEVEL WIBBLY WOBBLY UPDATER
def update(): # function that gets called every second to update assorted
    try:
        # note that this function needs to be as lightweight as possible, use if statements that avoid unnecessary work outside Osiris
        global foobarprev
        global photo
        # foobar currently playing widget
        foobarnow = [open("etc/foobar_nowplaying.txt","r").readlines()][0][0].rstrip("\n")[3:]
        if foobarnow.startswith("not running"):
            OSI.mpfoobarplaypause.configure(text="Foobar not running")
        elif foobarnow.startswith("paused:"):
            OSI.mpfoobarplaypause.configure(text="Paused")
        else:
            OSI.mpfoobarplaypause.configure(text="Playing")
        if foobarnow != foobarprev:
                image = Image.open(("/".join(foobarnow.lstrip("playing: ").split("\\")[:-1]))+"/albumArt.png")
                image = image.resize((100,100),Image.ANTIALIAS)
                photo = ImageTk.PhotoImage(image)
                OSI.mpfoobaralbart.configure(image=photo)

                maincolor = color_from_image(image)

                if (max(maincolor) + min(maincolor)) / 2 >= 127:
                    contrast = "#000000"
                else:
                    contrast = COLOR_TEXT

                bordercolor = RGBToHex(maincolor)
                OSI.mpfoobarwrapper.configure(bg=bordercolor)

                temp = foobarnow[len("playing: "):].split("\\")
                OSI.mpfoobarframe.configure(bg=bordercolor)
                OSI.mpfoobar_song.configure(text=temp[-1][3:-4], bg=bordercolor, fg=contrast)
                OSI.mpfoobar_artist.configure(text=temp[-3], bg=bordercolor, fg=contrast)
                OSI.mpfoobar_album.configure(text=temp[-2], bg=bordercolor, fg=contrast)
                OSI.mpfoobarplaypause.configure(bg=bordercolor, fg=contrast)
                # OSI.mpfoobartext.configure(text="Song:   "+temp[-1][3:-4]+"\nArtist: "+temp[-3]+"\nAlbum:  "+temp[-2])
                foobarprev = foobarnow[:]
        root.after(1000,update)
    except Exception as e:
        print(e)
        root.after(1000,update)


# MAIN WINDOW DEFINITION
class MainUI:
    def __init__(s,master):
        # some pre-op (can be anywhere in this init)
        s.pliactive = False
        s.entryhist = ['']
        s.entrypos = 0
        s.state = "max"

        s.mp_page = 0
        s.dl_page = 0

        # start of window definition and setup
        s.master = master
        master.title("Osiris")
        master.resizable(0,0)
        s.rootframe = tk.Frame(s.master,background=COLOR_BUTTON)

        s.mainframe = tk.Frame(s.rootframe,bg=COLOR_BUTTON)

        # time for the bulk of the widgets
        s.buttonframe = tk.Frame(s.mainframe,bg=COLOR_BUTTON,height=38)
        s.buttonframe.pack_propagate(0)

        # adding logo
        s.logoframe = tk.Frame(s.buttonframe, height=38, width=80,bg=COLOR_BUTTON)
        s.logoframe.pack_propagate(0)
        s.logoimage = Image.open("etc/background-white-logo.png")
        s.logoimage = s.logoimage.resize((57,30),Image.ANTIALIAS)
        s.logophoto = ImageTk.PhotoImage(s.logoimage)
        s.logolabel = tk.Label(s.logoframe, height=33, width=66, image=s.logophoto,bg=COLOR_BUTTON)
        s.logolabel.image = s.logophoto
        s.logolabel.pack(padx=10,pady=4)
        s.logoframe.pack(side=LEFT)

        # creating navbar buttons
        s.mpbutton = tk.Button(s.buttonframe,borderwidth=0,activebackground=COLOR_BUTTON_ACTIVE,activeforeground=COLOR_TEXT,font=FONT_L,width=TK_BUTTON_WIDTH,text="MUSIC",command=lambda:s.select("mp"))
        s.dbbutton = tk.Button(s.buttonframe,borderwidth=0,activebackground=COLOR_BUTTON_ACTIVE,activeforeground=COLOR_TEXT,font=FONT_L,width=TK_BUTTON_WIDTH,text="DATABASE",command=lambda:s.select("db"))
        s.dlbutton = tk.Button(s.buttonframe,borderwidth=0,activebackground=COLOR_BUTTON_ACTIVE,activeforeground=COLOR_TEXT,font=FONT_L,width=TK_BUTTON_WIDTH,text="DOWNLOAD",command=lambda:s.select("dl"))
        s.sebutton = tk.Button(s.buttonframe,borderwidth=0,activebackground=COLOR_BUTTON_ACTIVE,activeforeground=COLOR_TEXT,font=FONT_L,width=TK_BUTTON_WIDTH,text="SERVER STATUS",command=lambda:s.select("se"))
        s.stbutton = tk.Button(s.buttonframe,borderwidth=0,activebackground=COLOR_BUTTON_ACTIVE,activeforeground=COLOR_TEXT,font=FONT_L,width=TK_BUTTON_WIDTH,text="SETTINGS",command=lambda:s.select("st"))

        # list of buttons
        s.buttons = [s.mpbutton,s.dbbutton,s.dlbutton,s.sebutton,s.stbutton]

        # pack all buttons
        for i in s.buttons:
            i.pack(side=LEFT, fill=Y)

        # generate window controls if the user opted to omit the Windows navbar
        if settings["set_notitle"]=="True":
            s.exitbutton = tk.Button(s.buttonframe,borderwidth=0,bg=COLOR_BUTTON,activebackground="#c41313",fg=COLOR_TEXT,activeforeground="white",font=FONT_BOLD,width=4,text=" X ",command=root.destroy)
            s.exitbutton.bind("<Enter>", lambda x: s.exitbutton.configure(bg="#c41313"))
            s.exitbutton.bind("<Leave>", lambda x: s.exitbutton.configure(bg=COLOR_BUTTON))
            s.exitbutton.pack(side=RIGHT, fill=Y)
            # minimize not possible because of overrideredirect
            s.minbutton = tk.Button(s.buttonframe,borderwidth=0,bg=COLOR_BUTTON,activebackground=COLOR_BG_3,fg=COLOR_TEXT,activeforeground="white",font=FONT_BOLD,width=4,text=" _ ",command=s.attemptMinimise)
            s.minbutton.bind("<Enter>", lambda x: s.minbutton.configure(bg=COLOR_BG_3))
            s.minbutton.bind("<Leave>", lambda x: s.minbutton.configure(bg=COLOR_BUTTON))
            s.minbutton.pack(side=RIGHT, fill=Y)
        s.buttonframe.grid(column=0,columnspan=2,row=0,sticky=W+E)

        # the sandwich goes:
        #  contentwrapperframe
        #   scrollcanvas
        #    contentframe
        #     ALL FRAME WIDGETS (mp, db, dl)
        s.contentwrapperframe = tk.Frame(s.mainframe,bg=COLOR_BG_1,height=TK_HEIGHT-64,width=TK_WIDTH-306)
        s.scrollcanvas = tk.Canvas(s.contentwrapperframe,bg=COLOR_BG_1,yscrollincrement="1")
        s.scrollcanvas.pack(side=LEFT,fill=BOTH,expand=True)

        if settings["set_showscrollbar"]=="True":
            s.scrollbar = tk.Scrollbar(s.contentwrapperframe, command=s.scrollcanvas.yview)
            s.scrollbar.pack(side=RIGHT, fill=Y)
            s.scrollcanvas.config(yscrollcommand=s.scrollbar.set)

        s.contentframe = tk.Frame(s.scrollcanvas,bg=COLOR_BG_1)

        if settings["set_scrollable"]=="False":
            s.contentframe.pack(fill=BOTH,expand=True)

        if settings["set_scrollable"]=="True":
            s.scrollcanvas.create_window(0,0,window=s.contentframe,anchor="nw")
            s.scrollcanvas.bind_all("<MouseWheel>", s.mousewheel)

        s.logoimage = Image.open("etc/osi.png")

        s.mpframe = tk.Frame(s.contentframe,bg=COLOR_BG_1)

        # generate display for currently playing song
        if settings["set_foobarplaying"]=="True":
            s.mpfoobarwrapper = tk.Frame(s.mpframe,bg=COLOR_BUTTON)
            s.mpfoobarwrapper.place(x=1090, y=840,height=100,width=500)

            s.mpfoobarframe = tk.Frame(s.mpfoobarwrapper,bg=COLOR_BG_1)
            s.mpfoobaralbart = tk.Label(s.mpfoobarframe,bg=COLOR_BG_1)
            s.mpfoobaralbart.place(height=100,width=100)

            s.mpfoobar_song = tk.Label(s.mpfoobarframe,text="", width=35,anchor='w',font=FONT_BOLD_M,fg=COLOR_TEXT,bg=COLOR_BG_1)
            s.mpfoobar_song.place(x=105)
            s.mpfoobar_artist = tk.Label(s.mpfoobarframe,text="", width=35,anchor='w',font=FONT_ITALIC,fg=COLOR_TEXT,bg=COLOR_BG_1)
            s.mpfoobar_artist.place(x=105, y=30)
            s.mpfoobar_album = tk.Label(s.mpfoobarframe,text="", width=35,anchor='w',font=FONT_ITALIC,fg=COLOR_TEXT,bg=COLOR_BG_1)
            s.mpfoobar_album.place(x=105, y=60)

            s.mpfoobarplaypause = tk.Label(s.mpfoobarframe,text="",fg=COLOR_TEXT,font=FONT_S,width=10,anchor='e',bg=COLOR_BG_1)
            s.mpfoobarplaypause.place(x=405,y=70)
            s.mpfoobarframe.pack(side=TOP,pady=0,padx=0,fill=BOTH,expand=True)

        s.glbentry = tk.Entry(s.mainframe,font=FONT_L,bg=COLOR_BUTTON,fg=COLOR_TEXT,borderwidth=0,insertbackground=COLOR_TEXT)
        s.glbentry.bind("<Return>",lambda x:s.visentry(s.glbentry.get()))
        s.glbentry.bind("<Up>",lambda x:s.entrymove("up"))
        s.glbentry.bind("<Down>",lambda x:s.entrymove("down"))
        s.glbentry.grid(column= 0 , row = 2, sticky=W+E)
        s.glbentry.focus()

        s.dbframe = tk.Frame(s.contentframe,background=COLOR_BG_1)
        s.dbinfoframe = tk.Frame(s.dbframe)
        s.dbloclabel = tk.Label(s.dbinfoframe,bg=COLOR_BG_1, fg=COLOR_TEXT, font=FONT_M, text="Browsing: "+dbloc)
        s.dbloclabel.pack(side=LEFT)
        s.dbinfoframe.pack(side=TOP)
        s.dbeditorframe = tk.Frame(s.dbframe,bg=COLOR_BUTTON,highlightthickness=2,highlightbackground=COLOR_BG_3,highlightcolor=COLOR_BG_3,relief="flat")
        s.dbtitlewrapper = tk.Frame(s.dbeditorframe, bg=COLOR_BG_3)
        s.dbtitle = tk.Text(s.dbtitlewrapper,height=1,bd=0,font=(FONT_M[0],14),bg=COLOR_BUTTON,insertbackground=COLOR_TEXT,fg=COLOR_TEXT)
        s.dbtitle.pack(fill=X,pady=(0,2),padx=10)
        s.dbtitlewrapper.pack(fill=X)
        s.dbeditor = tk.Text(s.dbeditorframe,height=TK_LOG_HEIGHT,font=FONT_M,bg=COLOR_BUTTON,bd=0,insertbackground=COLOR_TEXT,fg=COLOR_TEXT,wrap="word")
        s.dbeditor.pack(padx=10,pady=5, fill=BOTH)

        # s.dbloadreq = tk.Label(s.dbframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=(FONT_M[0],"25"),text="ENTER TO LOAD DATABASE")
        # s.dbloadreq.pack(side=TOP,fill=BOTH,expand=True,padx=10,pady=10)

        s.dlframe = tk.Frame(s.contentframe,background=COLOR_BG_1)
        s.dlloginreq = tk.Label(s.dlframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=(FONT_M[0],"25"),text="LOGGING IN, PLEASE WAIT")
        s.dlloginreq.pack(side=TOP,fill=BOTH,expand=True,padx=10,pady=10)

        s.seframe = tk.Frame(s.contentframe,background=COLOR_BUTTON)
        s.seframe.grid_propagate(0)

        s.stframe = tk.Frame(s.contentframe,background=COLOR_BG_1)
        # key,label,col,row,type




        # one final thing: the log
        s.logframe = tk.Frame(s.mainframe,width=300,bg=COLOR_BG_1)
        s.loglabel = tk.Label(s.logframe,text="",font=FONT_L,height=TK_LOG_HEIGHT,bg=COLOR_BG_1,fg=COLOR_TEXT,anchor=W,justify=LEFT) #"SystemButtonFace",text="BAAAAH")
        s.loglabel.pack(pady=(0,2),fill=X,side=BOTTOM)

        s.logframe.grid(column=1,row=1,sticky="NESW",padx=(6,0),pady=0)
        s.logframe.pack_propagate(0)

        s.responsiveframe = tk.Frame(s.mainframe,height=26,width=300,bg=COLOR_BUTTON)
        s.responsiveframe.pack_propagate(0)
        s.responsivelabel = tk.Label(s.responsiveframe,text="",height=1,font=FONT_L,bg=COLOR_BUTTON,fg="white")
        s.responsivelabel.pack(side=LEFT)
        s.responsiveframe.grid(column=1,row=2,sticky=E)
        # main window definitions complete, now doing pre-op on the widgets
        # list of modes for convenience

        # lists of things
        s.modes = ["mp","db","dl","se","st"]
        s.frames = [s.mpframe,s.dbframe,s.dlframe,s.seframe,s.stframe]
        s.interpreters = [s.mpinterpret,s.dbinterpret,s.dlinterpret,s.seinterpret,s.stinterpret]

        s.focuslist = [s.dbeditor,s.glbentry]
        # commence the pre-op
        s.contentwrapperframe.grid(column=0,row=1)
        s.contentwrapperframe.pack_propagate(0)

        s.mainframe.grid(column=0,row=0,padx=0,pady=0)

        s.rootframe.pack()

        s.select("mp") # should be the last statement in this init
        # for i in s.frames:
        #     s.backgroundimage = Image.open("etc/background.png")
        #     s.backgroundphoto = ImageTk.PhotoImage(s.backgroundimage)
        #     s.background = tk.Label(i, image=s.backgroundphoto, bg=COLOR_BG_1)
        #     s.background.place(x=-250,y=-250,relx=0.5,rely=0.5)

# GENERAL DEFS
    def attemptMinimise(s):
        if s.state != "min":
            root.geometry("0x0")
            s.state = "forcemin"
            root.after(100,s.stateSetMin)
    def stateSetMin(s):
        s.state = "min"

    def attemptMaximise(s):
        if s.state == "min":
            root.geometry(geomwidth+"x"+geomheight+"+0+0")
            s.state = "max"


    def entrymove(s,updown): # handles changing the contents of the entry window
        if s.entrypos == 0:
            s.entryhist[0] = s.glbentry.get()
        if updown=="up" and s.entrypos!=len(s.entryhist)-1:
            s.glbentry.delete("0",len(s.glbentry.get()))
            s.glbentry.insert(END,s.entryhist[s.entrypos+1])
            s.entrypos += 1
        if updown=="down" and s.entrypos != 0:
            s.glbentry.delete("0",len(s.glbentry.get()))
            s.glbentry.insert(END,s.entryhist[s.entrypos-1])
            s.entrypos -= 1
        s.responsive()

    def tableft(s,event):
        OSI.select(OSI.modes[OSI.modes.index(OSI.mode)-1])
        return "break"
    def tabright(s,event):
        OSI.select(OSI.modes[(OSI.modes.index(OSI.mode)+1)%(len(OSI.modes))])
        return "break"

    def mousewheel(s,event):
        s.scrollcanvas.yview_scroll(-1*int(event.delta/5), "units")

    def log(s,tolog):
        oldlog = s.loglabel.cget('text')
        newlog = (TK_LOG_HEIGHT*[""]+oldlog.split("\n")+[str(tolog)])[-1*TK_LOG_HEIGHT:]
        s.loglabel.config(text="\n".join(newlog))

    def greet(s):
        curhour = datetime.datetime.now().hour
        if curhour >= 5 and curhour <=7:
            res = "Up early, sir?"
        elif curhour > 7 and curhour < 12:
            res = "Good morning sir"
        elif curhour >= 12 and curhour < 18:
            res = "Good afternoon sir"
        elif curhour >= 18 and curhour < 24:
            res = "Good evening sir"
        elif curhour < 2:
            res = "Consider sleeping, sir"
        elif curhour < 5:
            res = "Bed. Now."
        s.log("OSI: "+res)

    def select(s,choice):
        for i in s.frames: i.pack_forget()
        for i in s.buttons: i.configure(relief=RAISED,bg=COLOR_BUTTON,fg=COLOR_TEXT)

        # selecting the mode to switch to and applying appropriate widget changes
        s.modeindex = s.modes.index(choice)

        s.buttons[s.modeindex].configure(relief=SUNKEN,bg=COLOR_BUTTON_ACTIVE,fg=COLOR_TEXT)
        s.frames[s.modeindex].pack(fill=BOTH,expand=True,pady=TK_PADDING,padx=TK_PADDING)
        s.mode = choice

    def responsive(s):
        cur = s.glbentry.get()
        msg = ""
        if s.mode == "mp":
            if cur.rstrip(" ") == "": msg = ""
            elif cur == "c": msg = "Clear all"
            elif cur == "p": msg = "Play all"
            elif cur == "rf": msg = "Refresh library"
            elif cur == "e": msg = "Open foobar"
            elif cur == "pli": msg = "Open the playlist screen"
            elif cur == "plic": msg = "Close the playlist screen"
            elif cur in ["pl","pll"]: msg = "Please enter a playlist"
            elif cur == "gp": msg = "Select most recent GP song"
            elif cur == "bin": msg = "Send all to trash"
            elif cur.startswith("plsave "):
                msg = "Save this as a playlist"
            elif cur.startswith(("s ","p ","r ","d ", "bin ", "gp ","pl ","pll ")):
                flag = cur.split()[0]
                comm = " ".join(cur.split()[1:])
                if flag == "s":
                    msg = "Select " + str(len(match_criteria(comm,allfiles))) + " song(s)"
                if flag == "p":
                    if musicPaths == []:
                        msg = "Play " + str(len(match_criteria(comm,allfiles))) + " song(s)"
                    else:
                        msg = "Play " + str(len(match_criteria(comm,musicPaths))) + " song(s)"
                if flag == "r":
                    msg = "Refine to " + str(len(match_criteria(comm,musicPaths))) + " song(s)"
                if flag == "d":
                    msg = "Remove " + str(len(match_criteria(comm,musicPaths))) + " song(s)"
                if flag == "bin":
                    msg = "Send " + str(len(match_criteria(comm,musicPaths))) + " song(s) to trash"
                if flag == "gp":
                    if is_int(comm):
                        msg = "Select " + comm + " recent song(s)"
                    else:
                        if comm.rstrip(" ") != "":
                            msg = "Is '"+comm+"' a number, dick?"
                if flag == "pl":
                    if read_from_text("mp pl "+comm) != False:
                        msg = "Play " + str(len(read_from_text("mp pl "+comm))) + " songs"
                    else:
                        msg = "Unknown pl (try 'pli')"
                if flag == "pll":
                    if read_from_text("mp pl "+comm)  != False:
                        msg = "Load " + str(len(read_from_text("mp pl "+comm))) + " songs"
                    else:
                        msg = "Unknown pl (try 'pli')"
            else:
                if musicPaths == []:
                    msg = "Play " + str(len(match_criteria(cur,allfiles))) + " song(s)"
                else:
                    msg = "Play " + str(len(match_criteria(cur,musicPaths))) + " song(s)"
        elif s.mode == "gp":
            if cur == "dl":
                msg = "Download this selection"
        s.responsivelabel.config(text=msg)

    def visentry(s, command):
        s.log("USR: " + command)
        s.entryhist = [''] + [command] + s.entryhist[1:]
        s.entrypos = 0
        s.glbentry.delete("0",len(s.glbentry.get()))
        s.responsivelabel.configure(text="")

        s.invisentry(command)


    def invisentry(s, command): # execute an entry command as normal, but without logging or adding to entry history
        s.interpreters[s.modeindex](command)


#################################### MUSIC DEFS #####################################################################

    def mprefresh(s): # refreshes the database index in osData.txt
        '''diskdata = [os.path.join(settings["searchdir"],name)
            for settings["searchdir"], dirs, files in os.walk(settings["searchdir"])
            for name in files
            if name.endswith((".mp3",".flac",".m4a",".wav"))]'''

        diskdata = []
        for ftype in ALLOWED_FILETYPES:
            diskdata.extend(glob.glob(settings["searchdir"]+"**/*"+ftype, recursive = True))

        write_to_text(diskdata,"mp allfiles")
        s.mpfilesget()

    def mpfilesget(s): # updates allfiles and mp playcount using osData.txt
        global allfiles
        result = read_from_text("mp allfiles")
        if result != False:
            allfiles = result
        else:
            s.log("OSI: OwO little fucky wucky")
            s.log("OSI: pls restart")
            s.log("OSI: (mp allfiles in osData.txt)")

    def mpinterpret(s,entry): # interprets the given entry command in the context of the music player
        global musicPaths, mpWidgets
        s.entry = " ".join(entry.split())
        s.cflag = entry.split()[0]
        s.UI = entry[len(s.cflag)+1:]
        s.oldpaths = musicPaths[:]
        s.newpaths = musicPaths[:]

        # start by finding what the new desired paths are
        # also run code that doesn't influence paths, eg: playing, refreshing, saving
        if s.cflag == "s":
            s.newpaths = remove_duplicates(s.oldpaths+match_criteria(s.UI,allfiles))
            s.log("OSI: Added " + str(len(match_criteria(s.UI,allfiles))) + " song(s)")
        elif s.cflag == "r":
            s.newpaths = remove_duplicates(match_criteria(s.UI,s.oldpaths))
            s.log("OSI: Refined to " + str(len(s.newpaths)) + " song(s)")
        elif s.cflag == "d":
            s.newpaths = [x for x in s.oldpaths if x not in match_criteria(s.UI,s.oldpaths)]
            s.log("OSI: Removed " + str(len(s.oldpaths)-len(s.newpaths)) + " song(s)")
        elif s.cflag == "p":
            if s.UI == "" and s.oldpaths != []:
                s.mpplay(s.oldpaths)
            if s.UI != "":
                if s.oldpaths == []:
                    if len(match_criteria(s.UI,allfiles)) != 0:
                        s.mpplay(match_criteria(s.UI,allfiles))
                elif len(match_criteria(s.UI,s.oldpaths)) != 0:
                    s.mpplay(match_criteria(s.UI,s.oldpaths))
        elif s.cflag == "gp":
            s.gpsongs = [x for x in allfiles if "\\GP\\" in x.replace("/","\\")]
            s.gpsongs.sort(key=lambda x: os.path.getmtime(x))
            if s.UI == "": temp = -1
            else: temp = -1*int(s.UI)
            s.newpaths = remove_duplicates(s.gpsongs[temp:] + s.oldpaths)
        elif s.cflag == "bin":
            if s.UI == "":
                for i in s.oldpaths:
                    send2trash(i)
                s.log("OSI: Sent " + str(len(s.oldpaths)) + " song(s) to trash")
                s.newpaths = []
            else:
                for i in remove_duplicates(match_criteria(s.UI,s.oldpaths)):
                    send2trash(i)
                s.newpaths = [x for x in s.oldpaths if x not in match_criteria(s.UI,s.oldpaths)]
                s.log("OSI: Sent " + str(len(s.oldpaths)-len(s.newpaths)) + " song(s) to trash")
            s.mprefresh() # also updates local allfiles
        elif s.cflag == "e":
            s.mpplay([])
        elif s.cflag == "c":
            s.newpaths = []
            s.log("OSI: Cleared selection")
        elif s.cflag == "pg":
            if is_int(s.UI):
                s.mp_page = int(s.UI - 1) % ceil(len(mpWidgets)/MP_PAGE_SIZE)
        elif s.cflag == "pgn":
            s.mp_page = (s.mp_page + 1) % ceil(len(mpWidgets)/MP_PAGE_SIZE)
        elif s.cflag == "pgp":
            s.mp_page = (s.mp_page - 1) % ceil(len(mpWidgets)/MP_PAGE_SIZE)
        elif s.cflag == "pl":
            if read_from_text(str("mp pl "+s.UI)) != False:
                s.mpplay(read_from_text(str("mp pl "+s.UI)))
        elif s.cflag == "plsave":
            if len(s.oldpaths) == 0:
                #logappend("HMP: No song(s) selected")
                pass
            else:
                write_to_text(s.oldpaths,str("mp pl "+s.UI))
                s.log("OSI: Saved playlist")
                try:
                    s.mpinterpret("plic")
                    s.mpinterpret("pli")
                except:
                    pass
        elif s.cflag == "pldel":
            if del_text("mp pl "+s.UI):
                s.log("OSI: Playlist deleted")
            else:
                s.log("ERR: Playlist deletion failed")
        elif s.cflag == "pll":
            if read_from_text(str("mp pl "+s.UI)) != False:
                s.newpaths = remove_duplicates(s.oldpaths+read_from_text(str("mp pl "+s.UI)))
                s.log("OSI: Loaded " + s.UI)
        elif s.cflag == "rf":
            s.mprefresh()
            s.log("OSI: Refreshed library")
        elif s.cflag == "pli": # open the playlist information window
            if not s.pliactive:
                s.mpplgen()
                s.pliactive = True
        elif s.cflag == "plic": # close the playlist information window
            s.pliwrapper.place_forget()
            s.pliwrapper.destroy()
            s.pliactive = False
        else:
            if s.oldpaths == []:
                if len(match_criteria(s.cflag+" "+s.UI,allfiles)) != 0:
                    s.mpplay(match_criteria(s.cflag+" "+s.UI,allfiles))
            else:
                if len(match_criteria(s.cflag+" "+s.UI,s.oldpaths)) != 0:
                    s.mpplay(match_criteria(s.cflag+" "+s.UI,s.oldpaths))

        for i in range(len(s.newpaths)):
            s.newpaths[i] = "\\".join(s.newpaths[i].split("\\"))
            s.newpaths[i] = "\\".join(s.newpaths[i].split("/"))

        # now that the new paths are known, update the widgets accordingly
        for i in [x for x in s.newpaths if x not in s.oldpaths]:
            mpWidgets.append(MpWidget(i))

        if len(s.oldpaths) > 0 and len(s.newpaths) == 0:
            musicPaths = []
            for i in mpWidgets:
                i.mainframe.destroy()
            mpWidgets = []
        else:
            for i in [x for x in s.oldpaths if x not in s.newpaths]:
                mpWidgets[musicPaths.index(i)].remove(True) # incredibly inefficient
                OSI.mpupdate()

        # place any commands that should run after every entry below this line

        # decide which mpWidgets to show
        for i in mpWidgets:
            i.hide()
        for i in range((s.mp_page) * MP_PAGE_SIZE, min(len(mpWidgets), ((s.mp_page + 1) * MP_PAGE_SIZE))):
            mpWidgets[i].show()

        # update page handler
        s.mp_pageHandler.set_page(s.mp_page+1, len(mpWidgets))

        # raise playlist info widget above entries
        try: s.pliwrapper.tkraise()
        except: pass

    def mpupdate(s): # get all the MpWidget widgets to update themselves
        for i in mpWidgets: i.update()

    def mpplay(s,songlist): # function to play a list of .mp3 files with foobar
        #mpcount(songlist)
        s.log("OSI: Playing " + str(len(songlist)) + " song(s)")
        subprocess.Popen([settings["foobarexe"]]+[i for i in songlist], shell=False)

    def mpplgen(s): # generate the playlist info widget
        # define surrounding layout (regardless of playlists)
        s.pliwrapper = tk.Frame(s.mpframe,bg=COLOR_BUTTON)
        s.pliwrapper.pack_propagate(0)
        s.pliframe = tk.Frame(s.pliwrapper,bg=COLOR_BG_2)
        s.plikeyframe = tk.Frame(s.pliframe,width=260,height=22,bg=COLOR_BG_2)
        s.plikeyframe.pack_propagate(0)
        s.plikeyframe.pack(side=TOP,fill=X,pady=(0,1))
        s.plitextstring = "Name       #S  #A"
        if settings["set_pliduration"]=="True":
            s.plitextstring += "  Length"
        s.plikey = tk.Label(s.plikeyframe,font=FONT_M,text=s.plitextstring,bg=COLOR_BG_2,fg=COLOR_TEXT)
        s.plikey.pack(side=LEFT,anchor=W)
        s.plikeydel = tk.Button(s.plikeyframe,fg=COLOR_TEXT,font=FONT_M,borderwidth=0,text="X",command=lambda:s.mpinterpret("plic"),bg=COLOR_BUTTON)
        s.plikeydel.pack(side=RIGHT)
        # get all playlists + info
        s.plipllist = []  #'playlistinfoplaylistlist' i am excellent at naming things
        for i in search_text("mp pl "):
            s.plipllist.append([i[6:]]) # add name
            s.plipllist[-1].append(str(len(read_from_text(i)))) # add number of song(s)
            s.plipllist[-1].append(str(len(remove_duplicates([x.split("/")[-1].split("\\")[1] for x in read_from_text(i)])))) # add number of artists (mildly proud that this worked in one go)
            if settings["set_pliduration"]=="True":
                s.temp_length = sum([int(MP3(x).info.length) for x in read_from_text(i) if '.m4a' not in x])
                s.plipllist[-1].append(str(int(s.temp_length//60))+":"+str(int(s.temp_length%60)))

        for i in s.plipllist:
            pliLine(i)
        s.pliframe.pack(side=TOP,fill=Y,expand=True)
        s.pliwrapper.place(x=630,width=266,height=TK_HEIGHT)

#################################### DATABASE DEFS #####################################################################
    def dbinterpret(s,entry):
        global dbloc, dbkey
        if dbstate[0] == "password":
            if dbkey == False:
                dbkey = [entry,""]
                s.glbentry.delete("0",END)
            elif len(dbkey) == 2:
                if dbkey[1] == "":
                    dbkey[1] = entry
                    dbstate[0] = "browse"
                    s.glbentry.delete("0",END)
                    s.glbentry.configure(show="")
                    s.dbrefresh()
                    s.glbentry.bind("<Return>",lambda x:s.visentry(s.glbentry.get()))

        # when browsing
        elif dbstate[0] == "browse":
            flag = entry.split()[0]
            comm = " ".join(entry.split()[1:])

            if flag == "fulldecrypt" and len(dbkey) == 2: # fully decrypt all files in currect folder, changing only extensions.
                if comm == "affirmative "+dbkey[0]+";"+dbkey[1]:
                    # full decrypt confirmed and authorised
                    for i in [x for x in dbstate[1] if x.endswith(".aegis")]:
                        reading = open(rootdir+dbloc+i,"rb")
                        decdata = s.aegdec(dbkey,reading.read(-1))
                        writing = open(rootdir+dbloc+i+".txt","w")
                        writing.write(decdata)
                        reading.close()
                        writing.close()
                        send2trash(rootdir+dbloc+i)
            elif flag == "fullencrypt" and len(dbkey) == 2:
                if comm == "affirmative "+dbkey[0]+";"+dbkey[1]:
                    # full encrypt confirmed and authorised
                    for i in [x for x in dbstate[1] if x.endswith(".aegis.txt")]:
                        reading = open(rootdir+dbloc+i,"r")
                        encdata = s.aegenc(dbkey,reading.read(-1))
                        writing = open(rootdir+dbloc+i.rstrip(".txt"),"wb")
                        writing.write(encdata)
                        reading.close()
                        writing.close()
                        send2trash(rootdir+dbloc+i)
            elif flag in ["key","unlock"]: # decoding keys command
                if comm == "":
                    dbkey = False
                    dbstate[0] = "password"
                    s.glbentry.configure(show="*")
                    s.glbentry.bind("<Return>",lambda x:s.dbinterpret(s.glbentry.get()))
                elif len(comm.split(";")) == 2:
                    dbkey = comm.split(";")[:2]
                else:
                    s.log("OSI: Input 2 keys")

            elif flag == "lock": # delete keys
                dbkey = False

            elif flag in ["d","del","bin"]: # delete file / folder
                if comm != "":
                    target = match_criteria(comm, dbstate[1])
                    for i in target:
                        targetindex = dbstate[1].index(i)
                        i = dbstate[2][targetindex]
                        if dbstate[3][targetindex] in ["text","aegis","folder"]:
                            i = dbloc+i
                            send2trash(i)

            elif flag in ["nf","newf","nfol","newfol","newfolder"]: # create folder
                if comm not in dbstate[2]:
                    os.mkdir(dbloc+comm)

            elif flag in ["nt","newt","ntxt","newtxt","newtext"]: # create text file
                s.dbswitch()
                if comm == "":
                    dbloc += "*.txt"
                    s.dbtitle.focus_set()
                    s.dbloclabel.configure(text=("Editing: "+dbloc))
                else:
                    dbloc += comm+".txt"
                    s.dbtitle.insert("0.0",comm)
                    s.dbloclabel.configure(text=("Editing: "+dbloc))

            elif flag in ["na","newa","naeg","newaeg","newaegis"]: # create aegis file
                if dbkey != False:
                    s.dbswitch()
                    if comm == "":
                        dbloc += "*.aegis"
                        s.dbtitle.focus_set()
                        s.dbloclabel.configure(text=("Editing: "+dbloc))
                    else:
                        dbloc += comm+".aegis"
                        s.dbtitle.insert("0.0",comm)
                        s.dbloclabel.configure(text=("Editing: "+dbloc))
                else:
                    s.log("OSI: Key required")

            elif flag in ["u","up","b"]: # go up one or more folders
                if comm == "": comm = 2
                else: comm = int(comm) + 1
                dbloc = "/".join(dbloc.split("/")[0:max(-1*(len(dbloc.split("/"))-1), -comm)])+"/"

            elif flag == "root": # reset to root
                dbloc = DB_DIR


            else: # open aegis/text/folder
                if flag != "o":
                    comm = flag + " " + comm
                matchresult = match_criteria(comm,dbstate[1])
                if matchresult != []:
                    matchresult = matchresult[0]
                    matchindex = dbstate[1].index(matchresult)
                    if os.path.isdir(rootdir+dbloc+matchresult):
                        dbloc += match_criteria(comm,dbstate[1])[0]+"/"
                    else:
                        if dbstate[3][matchindex] == "text":
                            s.dbtitle.insert(END,matchresult)
                            dbloc += dbstate[2][matchindex]
                            ofile = open(rootdir+dbloc, "r")
                            lines = ("".join(ofile.readlines())).rstrip("\n")
                            ofile.close()
                            s.dbloclabel.configure(text=("Editing: "+dbloc))

                        elif dbstate[2][matchindex].endswith(".aegis"):
                            matchpath = dbstate[2][matchindex]
                            if dbkey != False:
                                try:
                                    dbloc += matchpath
                                    filedata = open(rootdir+dbloc, "rb")
                                    filedata = s.aegdec(dbkey,filedata.read(-1))
                                    title = filedata.split("\n\n")[0][6:]
                                    lines = "\n\n".join(filedata.split("\n\n")[1:])[5:].rstrip("\n")
                                    s.dbtitle.insert(END,title)
                                    s.dbloclabel.configure(text=("Editing: "+dbloc.rstrip(matchpath)+title+".aegis"))
                                except:
                                    s.log("OSI: Incorrect key")
                                    return
                            else:
                                s.log("OSI: Key required")
                                return

                        # presuming that file contents have been gotten, switch to edit mode
                        s.dbswitch()
                        # populate text editor
                        s.dbeditor.insert(END,lines)
                        s.log("OSI: File opened")
                        return

            if dbstate[0] == "browse":
                s.dbrefresh()

        # when editing
        elif dbstate[0] == "edit":
            flag = entry.split()[0]
            try: comm = " ".join(entry.split()[1:])
            except: pass

            if flag in ["s","save","b"]: # save and exit file

                if dbloc.endswith(".txt"):
                    dbloc = "/".join(dbloc.split("/")[:-1])+"/"+filter_chars(s.dbtitle.get("0.0",END),"\\/*<>:?\"|\n")+".txt"
                    writefile = open(rootdir+dbloc,"w")
                    writefile.write("\n".join(s.dbeditor.get("0.0",END).split("\n")[:-1]))
                    writefile.close()

                elif dbloc.endswith(".aegis"):
                    # assuming key is already entered, else we would not be editing an aegis file
                    if s.dbtitle.get("0.0",END).rstrip("\n") not in [x for x in dbstate[1] if dbstate[3][dbstate[1].index(x)].startswith("aegis")]:
                        # nonexistant title: new file
                        dbloc = "/".join(dbloc.split("/")[:-1])+"/"+str(random())+".aegis"
                    writedata = "title:"+s.dbtitle.get("0.0",END).rstrip("\n")+"\n\ndata:"
                    writedata += "\n".join(s.dbeditor.get("0.0",END).split("\n")[:-1])
                    writedata = s.aegenc(dbkey,writedata)
                    writefile = open(dbloc,"wb")
                    writefile.write(writedata)
                    writefile.close()
            if flag in ["s","save","b","ns","nosave"]:
                # clear the editor
                s.dbeditor.delete("0.0",END)
                s.dbtitle.delete("0.0",END)
                s.dbswitch()
                dbloc = "/".join(dbloc.split("/")[:-1])+"/"
                s.dbrefresh()

    def aegkeyparse(s,keys,first):
        endkey = ""
        for i in range(32):
            if first: endkey += (keys[i%2]*32)[i//2]
            if not first: endkey += (keys[(i+1)%2][::-1]*32)[i//2]
        return str.encode(endkey)

    def aegenc(s,keys,data):
        data = str.encode(data)
        for i in range(DB_ENC_LEVEL): data = s.aegenc_single(s.aegkeyparse(keys,True),data)
        for i in range(DB_ENC_LEVEL): data = s.aegenc_single(s.aegkeyparse(keys,False),data)
        return data

    def aegdec(s,keys,data):
        for i in range(DB_ENC_LEVEL): data = s.aegdec_single(s.aegkeyparse(keys,False),data)
        for i in range(DB_ENC_LEVEL): data = s.aegdec_single(s.aegkeyparse(keys,True),data)
        data = data.decode()
        return data

    def aegenc_single(s,key,data):
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return (cipher.nonce+tag+ciphertext)

    def aegdec_single(s,key,data):
        nonce = data[:16]
        tag = data[16:32]
        ciphertext = data[32:]
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        output = cipher.decrypt_and_verify(ciphertext, tag)
        return output

    def dbswitch(s):
        global dbstate, dbWidgets
        if dbstate[0] == "browse":
            [x.wrapper.destroy() for x in dbWidgets]
            dbWidgets = []
            s.dbeditorframe.pack(fill=BOTH)
            dbstate[0] = "edit"
        elif dbstate[0] == "edit":
            s.dbeditorframe.pack_forget()
            dbstate[0] = "browse"

    def dbfocusedit(s,event):
        s.dbeditor.focus_set()
        return "break"
    def dbfocusentry(s,event):
        s.glbentry.focus_set()
        return "break"

    def dbrefresh(s):
        global dbstate
        # wipe dbstate
        dbstate = [dbstate[0],[],[],[]]
        # wipe current widgets
        [x.wrapper.destroy() for x in dbWidgets]
        s.dbloclabel.configure(text="Browsing: "+dbloc)
        dbtotal = os.listdir(rootdir+dbloc)
        dbtext = [x for x in dbtotal if x.endswith(".txt")] # files
        sorted(dbtext, key=str.lower)
        dbaegis = [x for x in dbtotal if x.endswith(".aegis")]
        dbfolders = [x for x in dbtotal if os.path.isdir(rootdir+dbloc+x)] # folders
        sorted(dbfolders, key=str.lower)

        # run through folders
        while len(dbfolders) > 0:
            dbstate[1].append(dbfolders.pop(0))
            dbstate[2].append(dbstate[1][-1])
            dbstate[3].append("folder")
            dbWidgets.append(dbLine(dbstate[1][-1], len(dbstate[1])-1))

        # run through aegis
        tempshow = []
        temppath = []
        tempmap = []
        while len(dbaegis) > 0:
            if dbkey == False:
                tempshow.append("")
                temppath.append(dbaegis.pop(0))
                tempmap.append("aeg_nokey")
            else:
                try:
                    filedata = open(rootdir+dbloc+dbaegis[0], "rb")
                    filedata = s.aegdec(dbkey,filedata.read(-1))
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
            dbstate[1].append(tempshow.pop(curindex))
            dbstate[2].append(temppath.pop(curindex))
            dbstate[3].append(tempmap.pop(curindex))
            dbWidgets.append(dbLine(dbstate[2][-1], len(dbstate[1])-1))

        # run through text
        while len(dbtext) > 0:
            dbstate[1].append(dbtext.pop(0).rstrip(".txt"))
            dbstate[2].append(dbstate[1][-1]+".txt")
            dbstate[3].append("text")
            dbWidgets.append(dbLine(dbstate[2][-1], len(dbstate[1])-1))



#################################### DOWNLOAD DEFS #####################################################################
    def dlinterpret(s,entry):
        s.glbentry.delete("0",len(s.glbentry.get())) # empty the entry field

        if entry.startswith("d ") and is_int(entry.split()[1]): # if entry is delete command
            # del
            pass

        elif entry.startswith("pg "):
            if is_int(entry[3:]):
                s.dl_page = int(int(entry[3:]) - 1) % ceil(len(mpWidgets)/MP_PAGE_SIZE)

        elif entry == "pgn":
            s.dl_page = (s.dl_page + 1) % ceil(len(dlWidgets)/DL_PAGE_SIZE)

        elif entry == "pgp":
            s.dl_page = (s.dl_page - 1) % ceil(len(dlWidgets)/DL_PAGE_SIZE)

        elif entry == "dl":
            # go through all open widgets and tell them to ready
            for dl in dlWidgets:
                dl.ready()
            for dl in dlWidgets:
                del dlWidgets[dlWidgets.index(dl)]
            DLMAN.download()

        elif entry.startswith("yt "): # yt single song
            query = "+".join(entry[3:].split())
            res = requests.get("https://www.googleapis.com/youtube/v3/search?part=snippet&q="+query+"&type=video&key="+settings["yt_api_key"])
            data = res.json()["items"][:DL_ALTERNATIVES]
            dlWidgets.append(YtSingle([s.yt_get_track_data(x) for x in data]))

        elif entry.startswith(("album ")) and gplogin != False:
            search_results = s.gpsearch_album(entry[6:])
            if search_results != False:
                dlWidgets.append(GpAlbum(search_results))

        elif entry.startswith(("http://","https://","www.","youtube.com","play.google")):
            # if true, start parsing URL
            # remove unnecessary prefixes
            urlentry = entry
            for i in ["http://","https://","www.","youtube.com","play.google",".com","/music/"]:
                urlentry = urlentry.split(i)[-1]

            # for GP: note that album ids start with "B" and tracks start with "T"
            type = "none"
            id = "-"
            if "play.google" in entry and gplogin != False:
                if urlentry.startswith("m/T"): # track URL
                    id = urlentry[2:].split("?t=")[0]
                    type = "gp track"
                if urlentry.startswith("m/B"): # album URL
                    id = urlentry[2:].split("?t=")[0]
                    type = "gp album"
                if urlentry.startswith("playlist/"):
                    id = urlentry[9:-6] + "=="
                    type = "gp playlist"

            elif "youtube" in entry:
                if urlentry.startswith("/playlist?list="):
                    id = urlentry[15:]
                    type = "yt playlist"
                if urlentry.startswith("/watch?v="):
                    id = urlentry[9:]
                    type = "yt track"
            else:
                s.log("URL parsing failed")
            s.log("OSI: URL parsed")

            if type == "gp track":
                dlWidgets.append(GpTrack([s.gp_get_track_data(api.get_track_info(id))]))

            if type == "gp playlist":
                search_result = api.get_shared_playlist_contents(id)
                web_result = webapi.get_shared_playlist_info(id)
                pl_info = [
                            filter_(web_result["title"]),
                            filter_(web_result["author"]),
                            str(web_result["num_tracks"]),
                            filter_(web_result["description"]),
                          ]
                dlWidgets.append(GpPlaylist([s.gp_get_track_data(x["track"]) for x in search_result],pl_info))

            if type == "gp album":
                dlWidgets.append(GpAlbum([s.gp_get_album_data(api.get_album_info(id, False))]))

            if type == "yt track":
                trackres = requests.get("https://www.googleapis.com/youtube/v3/videos?part=snippet&id="+id+"&key="+settings["yt_api_key"])
                dlWidgets.append(YtSingle([s.yt_get_track_data(trackres.json()["items"][0])]))

            if type == "yt playlist":
                plres = requests.get("https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&id="+id+"&key="+settings["yt_api_key"])
                pldata = plres.json()["items"][0]
                pldata_parsed = [pldata["snippet"]["title"], pldata["snippet"]["channelTitle"], pldata["contentDetails"]["itemCount"]]

                initial_trackres = requests.get("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&maxResults=50&playlistId="+id+"&key="+settings["yt_api_key"])
                initial_trackdata = initial_trackres.json()["items"]
                if pldata_parsed[int(2)] > 50:
                    # if data longer than what can be gotten from 1 request, keep going
                    pagetoken = initial_trackres.json()["nextPageToken"]
                    while 1:
                        next_trackres = requests.get("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&maxResults=50&playlistId="+id+"&pageToken="+pagetoken+"&key="+settings["yt_api_key"])
                        initial_trackdata += next_trackres.json()["items"]
                        try: pagetoken = next_trackres.json()["nextPageToken"]
                        except: break
                dlWidgets.append(YtMulti([s.yt_get_track_data(x) for x in initial_trackdata], pldata_parsed))


        elif entry != "" and gplogin != False:
            # not a command or URL: default behaviour is to search GP for single track
            search_results = s.gpsearch_track(entry)
            if search_results != False:
                dlWidgets.append(GpTrack(search_results))

        # decide which dlWidgets to show
        for i in dlWidgets:
            i.hide()

        for i in range((s.dl_page) * DL_PAGE_SIZE, min(len(dlWidgets), ((s.dl_page + 1) * DL_PAGE_SIZE))):
            dlWidgets[i].show()

        # update page handler
        s.dl_pageHandler.set_page(s.dl_page+1, len(dlWidgets))

    def dl_delete(s, object):
        dlWidgets.pop(dlWidgets.index(object)).wrapper.destroy()

    def gpbackgroundlogin(s):
        global Mobileclient, Webclient
        from gmusicapi import Mobileclient, Webclient
        global gplogin
        global api
        global webapi
        api = Mobileclient()
        webapi = Webclient()
        try:
            gptemp = api.login(settings["gpemail"], gppass, settings["gpMAC"])
            gptemp2 = webapi.login(settings["gpemail"], gppass)
        except Exception as e:
            s.dlloginreq.configure(text="LOGIN FAILED")
            print(e)
            return
        gplogin = gptemp
        OSI.log("OSI: GP logged in")
        if gplogin == True:
            s.dlloginreq.pack_forget()
            DLMAN.mainframe.pack(side=BOTTOM, fill=X, pady=(10,0))
        OSI.dl_pageHandler = PageHandler("dl", DL_PAGE_SIZE)
        time.sleep(1)
        OSI.log("OSI: All systems nominal")

    def findborders(s, image):
        bordertop = 0
        borderbottom = 0
        borderleft = 0
        borderright = 0
        imgwidth = image.size[0]
        imgheight = image.size[1]
        for row in range(int(imgheight / 4)): # look through top quarter of image
            blacks = 0
            for col in range(imgwidth):
                (r,g,b) = image.getpixel((col,row))
                if r+g+b < DL_CROP_THRESH:
                    blacks += 1
            if imgwidth - blacks > 10: # if row is not primarily black, halt search here
                break
        bordertop = row

        for row in reversed(range(3 * int(imgheight / 4), imgheight)): # look through bottom quarter of image
            blacks = 0
            for col in range(imgwidth):
                (r,g,b) = image.getpixel((col,row))
                if r+g+b < DL_CROP_THRESH:
                    blacks += 1
            if imgwidth - blacks > 10: # if row is not primarily black, halt search here
                break
        borderbottom = row

        for col in (range(int(imgwidth / 4))): # look through left of the image
            blacks = 0
            for row in range(imgheight):
                (r,g,b) = image.getpixel((col,row))
                if r+g+b < DL_CROP_THRESH:
                    blacks += 1
            if imgheight - blacks > 10: # if row is not primarily black, halt search here
                break
        borderleft = col

        for col in reversed(range(3 * int(imgwidth / 4), imgwidth)): # look through bottom quarter of image
            blacks = 0
            for row in range(imgheight):
                (r,g,b) = image.getpixel((col,row))
                if r+g+b < DL_CROP_THRESH:
                    blacks += 1
            if imgheight - blacks > 10: # if row is not primarily black, halt search here
                break
        borderright = col

        return (borderleft,bordertop,  borderright,borderbottom)


    def yt_get_track_data(s, track):
        try: vid_id = track["contentDetails"]["videoId"]
        except:
            try: vid_id = track["id"]["videoId"]
            except: vid_id = track["id"]

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

    def gpsearch_track(s,query):
        # perform search of gp database
        try:
            results = api.search(query).get("song_hits",DL_ALTERNATIVES)[:DL_ALTERNATIVES]
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

    def gpsearch_album(s,query):
        # perform search of gp database
        try:
            results = api.search(query).get("album_hits",DL_ALTERNATIVES)[:DL_ALTERNATIVES]
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

    def dl_url2file(s,url,filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # open in binary mode
        with open(filename, "wb") as wfile:
            # get request
            response = requests.get(url)
            # write to file
            wfile.write(response.content)

    def gptagify(s,songpath,tinfo):
        tagfile = EasyMP3(songpath)
        tagfile["title"] = tinfo[0]
        tagfile["artist"] = tinfo[1]
        tagfile["albumartist"] = tinfo[1]
        tagfile["album"] = tinfo[2]
        tagfile["tracknumber"] = ('00'+str(tinfo[4]))[-2:]
        tagfile["composer"] = tinfo[6]
        tagfile["date"] = tinfo[7]
        tagfile["bpm"] = tinfo[8]
        tagfile["genre"] = tinfo[9]
        tagfile.save()

    def dlalbumartify(s,songpath,imagepath):
        audio = MP3(songpath, ID3=ID3)
        try:audio.add_tags()
        except:pass
        audio.tags.add(APIC(
                encoding=3, # 3 is for utf-8
                mime='image/png', # image/jpeg or image/png
                type=3, # 3 is for the cover image
                desc=u'Cover',
                data=open((imagepath),'rb').read()))
        audio.save()


    #################################### WORK DEFS #####################################################################

    def seinterpret(s,entry):
        s.log("Under construction")



    #################################### SETTINGS DEFS #####################################################################

    def stinterpret(s,entry):
        pass

    def promptSetting(s,key,type):
        if type == "file":
            newval = tk.filedialog.askopenfilename(initialdir="/".join(settings[key].split("/")[:-1]))
        elif type == "folder":
            newval = tk.filedialog.askdirectory(initialdir="/".join(settings[key].split("/")[:-2]))+"/"
        if newval not in ["","/"]:
            settings[key] = newval
            s.updateSettings()

    def switchSetting(s,key):
        settings[key] = str(settings[key] == "False")
        s.updateSettings()

    def cycleSetting(s,key,optionskey): # cycle through a list of options, setting key to the value that comes after the current one
        options = settings[optionskey].split(";")
        current = settings[key]
        if current in options:
            next = options[(options.index(current) + 1) % len(options)]
        else:
            next = options[0]
        settings[key] = next
        s.updateSettings()

    def updateSettings(s):
        for i in s.StWidgets: i.update()
        export_settings()


    #################################### END OF MainUI #####################################################################

class PageHandler:
    def __init__(s, mode, page_size):
        s.mode = mode
        s.page_size = page_size

        s.root = OSI.frames[OSI.modes.index(s.mode)]
        s.interpreter = OSI.interpreters[OSI.modes.index(s.mode)]

        s.mainframe = tk.Frame(s.root, bg=COLOR_BUTTON,height=30, width = 400)
        s.mainframe.pack_propagate(0)


        s.prev_button = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, borderwidth=0, activebackground=COLOR_BUTTON_ACTIVE, activeforeground=COLOR_TEXT, font=FONT_M, text="PREVIOUS", width=10, command=s.prev)
        s.prev_button.pack(side=LEFT)

        s.next_button = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, borderwidth=0, activebackground=COLOR_BUTTON_ACTIVE, activeforeground=COLOR_TEXT, font=FONT_M, text="NEXT", width=10, command=s.next)
        s.next_button.pack(side=RIGHT)

        s.current_page = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, width=10, text="PAGE 1")
        s.current_page.pack(side=TOP)



    def set_page(s, new, widget_count):
        if widget_count > s.page_size and not s.mainframe.winfo_ismapped():
            s.mainframe.pack(side=BOTTOM)
        if widget_count <= s.page_size and s.mainframe.winfo_ismapped():
            s.mainframe.pack_forget()
        s.current_page.configure(text="PAGE " + str(new))

    def prev(s):
        s.interpreter("pgp")

    def next(s):
        s.interpreter("pgn")

class DownloadManager:
    def __init__(s):
        s.mainframe = tk.Frame(OSI.dlframe,bg=COLOR_BUTTON,height=35, width=TK_PROGRESS_BAR_WIDTH)
        s.mainframe.pack_propagate(0)
        s.progress_bar_wrapper = tk.Frame(s.mainframe, bg=COLOR_BG_1)
        s.progress_bar_wrapper.place(width=TK_PROGRESS_BAR_WIDTH, height=3)
        s.progress_bar_wrapper.pack_propagate(0)
        s.progress_bar_done = tk.Frame(s.progress_bar_wrapper, bg="green", height=3, width=0, bd = 0)
        s.progress_bar_busy = tk.Frame(s.progress_bar_wrapper, bg="#469bfc", height=3, width=0, bd = 0)
        s.progress_bar_queued = tk.Frame(s.progress_bar_wrapper, bg="grey", height=3, width=0, bd = 0)
        for i in [s.progress_bar_done, s.progress_bar_busy, s.progress_bar_queued]:
            i.pack_propagate(0)

        s.state = "waiting"
        s.idle = True
        s.count_gpcomplete = 0
        s.count_gptotal = 0
        s.count_ytcomplete = 0
        s.count_yttotal = 0
        s.count_convtotal = 0
        s.GpTracks = []
        s.yttracks = []
        s.staticlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=40)
        s.staticlabel.pack(side=LEFT,pady=(1,0))
        s.gplabel = tk.Label(s.mainframe, bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=4,text="GP: ")
        s.gplabel.pack(side=LEFT,pady=(1,0))
        s.gpstatus = tk.Label(s.mainframe, bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=7)
        s.gpstatus.pack(side=LEFT,pady=(1,0))
        s.ytlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=6,text="  YT: ")
        s.ytlabel.pack(side=LEFT,pady=(1,0))
        s.ytstatus = tk.Label(s.mainframe, bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=7)
        s.ytstatus.pack(side=LEFT,pady=(1,0))
        s.convlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=14,text="  Converting: ")
        s.convlabel.pack(side=LEFT,pady=(1,0))
        s.convstatus = tk.Label(s.mainframe, bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=10)
        s.convstatus.pack(side=LEFT,pady=(1,0))
        s.refreshvalues()
        # mainframe not packed (this is done by login method)

    def refreshvalues(s): # update the tracking labels
        if s.state == "waiting":
            s.staticlabel.configure(text="Status: ready to download")
        if s.state == "downloading gp":
            s.staticlabel.configure(text="Status: downloading from Google Play")
        if s.state == "downloading yt":
            s.staticlabel.configure(text="Status: downloading from YouTube")
        dltotal = s.count_gptotal + s.count_yttotal
        if dltotal > 0:
            if not s.bars_packed:
                for i in [s.progress_bar_done, s.progress_bar_busy, s.progress_bar_queued]:
                    i.pack(side=LEFT)
                s.bars_packed = True
            if s.state == "waiting":
                s.progress_bar_done.configure(width=TK_PROGRESS_BAR_WIDTH*(max(0,(s.count_gpcomplete+s.count_ytcomplete))/dltotal))
                s.progress_bar_busy.configure(width=0)
            else:
                s.progress_bar_done.configure(width=TK_PROGRESS_BAR_WIDTH*(max(0,(s.count_gpcomplete+s.count_ytcomplete-1))/dltotal))
                s.progress_bar_busy.configure(width=TK_PROGRESS_BAR_WIDTH/dltotal)
            s.progress_bar_queued.configure(width=TK_PROGRESS_BAR_WIDTH*(max(0,(dltotal-s.count_gpcomplete-s.count_ytcomplete))/dltotal))
        else:
            s.bars_packed = False
            for i in [s.progress_bar_done, s.progress_bar_busy, s.progress_bar_queued]:
                i.pack_forget()
        s.gpstatus.configure(text=str(s.count_gpcomplete)+"/"+str(s.count_gptotal))
        s.ytstatus.configure(text=str(s.count_ytcomplete)+"/"+str(s.count_yttotal))
        s.convstatus.configure(text=str(s.count_convtotal)+" tracks")

    def download(s): # publicly accessible download command that is split into further tasks
        if len(s.GpTracks) + len(s.yttracks) > 0:
            if len(s.GpTracks) > 0:
                s.state = "downloading gp"
            else:
                s.state = "downloading yt"
            s.process_downloads() # start a continuously refreshing loop until all queues are done
        else:
            OSI.log("OSI: Nothing to download")

    def process_downloads(s): # function that updates the downloading process
        # process the top of the gp queue
        if s.idle and len(s.GpTracks) + len(s.yttracks) > 0:
            if len(s.GpTracks) > 0:
                threading.Thread(target=lambda: s.gp_download(s.GpTracks.pop(0))).start()
            elif len(s.yttracks) > 0:
                threading.Thread(target=lambda: s.yt_download(s.yttracks.pop(0))).start()

        # decide if we need to keep downloading
        if len(s.GpTracks) + len(s.yttracks) > 0:
            root.after(50,s.process_downloads) # continue the loop
        elif s.idle and s.count_convtotal == 0:
            s.count_gpcomplete = 0
            s.count_gptotal = 0
            s.count_ytcomplete = 0
            s.count_yttotal = 0
            s.state = "waiting"
            root.after(200,lambda: OSI.mprefresh())
            OSI.log("OSI: All downloads finished")
        else: # if idle but converting: wait a bit longer
            root.after(100,s.process_downloads)
        s.refreshvalues()

    def yt_download(s, track): # download from youtube data to filename
        s.idle = False
        s.count_ytcomplete += 1
        s.refreshvalues()
        url = track[3]
        track[1] = s.get_correct_channel_name(track)
        name = settings["dldir"]+"/YouTube/"+track[1]+"/"+track[0]+".mp3"
        os.makedirs(os.path.dirname(name), exist_ok=True)
        if not(os.path.isfile(name)):
            root.after(100, lambda: s.idle_conv_watchdog(url, name, track))
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(DL_POPEN_ARGS+[url], startupinfo=startupinfo)
        else:
            OSI.log("OSI: YT DL skipped")
            s.idle = True
            s.refreshvalues()
            return

    def generate_image_data(s, tracklist, _index=None):
        if _index != None:
            curinfo = tracklist[_index]
        else:
            curinfo = tracklist[0]
        image = Image.open(BytesIO(requests.get(curinfo[2]).content))
        borders = OSI.findborders(image)
        image = image.crop(borders) # crop image to borders
        maincolor = color_from_image(image) # get the prevalent color
        background = Image.new("RGB", (480,480),maincolor)
        background.paste(image, (borders[0],60+borders[1]))
        if _index != None:
            tracklist[_index].append(background.copy())
            tracklist[_index].append(maincolor)
        else:
            return background.copy()

    def idle_conv_watchdog(s, id, name, track, recursing = False): # keeps UI up to date and renames file when done
        for i in os.listdir():
            if i.endswith(id+".mp3"):
                if os.path.getsize(i) < 100 and not recursing: # found a match
                    s.idle = True
                    s.count_convtotal += 1
                    recursing = True
                elif os.path.getsize(i) > 1 and len([x for x in os.listdir() if id in x]) == 1:
                    try:
                        os.rename(i,name)
                        imagepath = "/".join(name.split("/")[:-1])+"/"+id+".png"
                        s.generate_image_data([track]).save(imagepath)
                        OSI.dlalbumartify(name, imagepath)
                        file_data = [track[0], track[1], "YouTube", "", "01", "", "None", "None", "Unknown", "Educational"]
                        OSI.gptagify(name, file_data)
                        s.count_convtotal -= 1
                        s.refreshvalues()
                        return
                    except:
                        print("Rename failed, we'll get em next time")
        s.refreshvalues()
        root.after(100, lambda: s.idle_conv_watchdog(id, name, track, recursing)) # else, keep looking

    def get_correct_channel_name(s, track):
        trackres = requests.get("https://www.googleapis.com/youtube/v3/videos?part=snippet&id="+track[3]+"&key="+settings["yt_api_key"])
        actual_channel = trackres.json()["items"][0]["snippet"]["channelTitle"]
        return actual_channel

    def gp_download(s,track): # download a single track
        s.idle = False
        s.count_gpcomplete += 1
        s.refreshvalues()
        '''
        track contents by index:
            (0) title
            (1) artist
            (2) album
            (3) album art URL
            (4) track number
            (5) storeId (was: multiIndex)
            (6) composer
            (7) date
            (8) bpm
            (9) genre
            (10) query
        '''

        folderpath = settings["dldir"] + track[1] + "/" + track[2] + "/"
        songpath = folderpath + ('00'+track[4])[-2:] + " " + track[0] + ".mp3"
        if os.path.isfile(songpath) and os.path.getsize(songpath) > 0:
            OSI.log("OSI: Skipping (already downloaded)")
        else:
            OSI.dl_url2file(str(api.get_stream_url(track[5])),songpath)
            if "albumArt.png" not in os.listdir(folderpath):
                try:
                    OSI.dl_url2file(track[3],(folderpath+"/albumArt.png"))
                except:
                    OSI.dl_url2file(result.get("albumArtRef")[0].get("url"),(folderpath+"/albumArt.png"))
            OSI.dlalbumartify(songpath,folderpath+"/albumArt.png")
            OSI.gptagify(songpath,track)

        s.idle = True

    def queue_gp(s,tracklist): # add tracks to the gp queue
        for i in tracklist:
            s.GpTracks.append(i)
            s.count_gptotal += 1
        s.refreshvalues()

    def queue_yt(s,tracklist): # add tracks to the yt queue
        for i in tracklist:
            s.yttracks.append(i)
            s.count_yttotal += 1
        s.refreshvalues()

class DlWidget: # ABSTRACT
    def __init__(s):
        # root superclass constructor has the elements shared by all possible variations of downloader widget
        # create root window with basic border
        s.wrapper = tk.Frame(OSI.dlframe,height=54)
        s.mainframe = tk.Frame(s.wrapper,bg=COLOR_BUTTON) # placeholder mainframe that is replaced by the generate function
        s.mainframe.pack(side=TOP,fill=X,padx=2,pady=2)

    def __str__(s):
        return "dbLine (INTERFACE!)"

    def generate(s):
        # every generate function should at least destroy the mainframe and replace it with its own
        s.mainframe.destroy()
        s.mainframe = tk.Frame(s.wrapper,bg=COLOR_BUTTON)
        s.mainframe.pack(side=TOP,fill=X,padx=2,pady=2)
        try: s.multiframe.destroy()
        except: pass # no multiframe to destroy

    def show(s):
        s.wrapper.pack(side=TOP,pady=(10,0),padx=10,fill=X)

    def hide(s):
        if s.wrapper.winfo_ismapped():
            s.wrapper.pack_forget()

    def set_color(s,color):
        if type(color) != str and len(color) == 3:
            color = RGBToHex(color)
        s.wrapper.configure(bg=color)

    def multipack(s):
        s.multibutton.configure(command=s.multiforget)
        s.multiframe.pack(side=TOP,fill=X)

    def multiforget(s):
        s.multibutton.configure(command=s.multipack)
        s.multiframe.pack_forget()

class GpLine(DlWidget):
    def __init__(s):
        DlWidget.__init__(s)

    def __str__(s):
        return "GpLine (INTERFACE!)"

class GpTrack(GpLine):
    def __init__(s, tracklist):
        GpLine.__init__(s)
        s.tracklist = tracklist
        s.multi_index = 0 # which song to select in the tracklist
        s.generate()

    def __str__(s):
        return "GpTrack"

    def generate(s): # use tracklist and multi_index to generate the widget as desired
        DlWidget.generate(s) # regenerate mainframe

        curinfo = s.tracklist[s.multi_index]
        s.image = Image.open(BytesIO(requests.get(curinfo[3]).content))
        s.image = s.image.resize((50,50), Image.ANTIALIAS)
        # get the main color from the image for fancy reasons
        s.bordercolor = color_from_image(s.image)

        if (max(s.bordercolor) + min(s.bordercolor)) / 2 >= 127:
            s.bordercontrast = "#000000"
        else:
            s.bordercontrast = COLOR_TEXT
        s.bordercolor = RGBToHex(s.bordercolor)
        s.typelabel = tk.Label(s.mainframe, bg=s.bordercolor,fg=s.bordercontrast,anchor=CENTER,font=(FONT_M[0], FONT_M[1], 'bold'),width=8,text="Track")
        s.typelabel.pack(side=LEFT,fill=Y)

        s.set_color(s.bordercolor)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe,height=50,width=50,bg=COLOR_BUTTON)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe,anchor=W,image=s.photo,borderwidth=0,highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=28,text=curinfo[0])
        s.titlelabel.pack(side=LEFT,padx=(10,0))
        s.artistlabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=28,text=curinfo[1])
        s.artistlabel.pack(side=LEFT,padx=(10,0))
        s.albumlabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=28,text=curinfo[2])
        s.albumlabel.pack(side=LEFT,padx=(10,0))
        s.delbutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="X",width=3,relief='ridge',bd=2,activebackground="#c41313",activeforeground=COLOR_TEXT, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=lambda: OSI.dl_delete(s))
        s.delbutton.pack(side=RIGHT,padx=(0,8))
        s.readybutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="OK",width=3,relief='ridge',bd=2,activebackground="green",activeforeground=COLOR_TEXT, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=s.ready)
        s.readybutton.pack(side=RIGHT,padx=(0,8))

        if len(s.tracklist) > 1: # if we actually have alternatives to show, make the multilist
            s.multibutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="ALT",width=5,relief='ridge',bd=2,highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,activebackground=COLOR_BUTTON,activeforeground=COLOR_TEXT,command=s.multipack)
            s.multibutton.pack(side=RIGHT,padx=(0,8))
            s.multiframe = tk.Frame(s.wrapper,bg=s.wrapper.cget("bg")) # indeed not packed, that is done by the multibutton
            for i in range(len(s.tracklist)):
                if i != s.multi_index: # only generate multilines for nonselected tracks
                    s.GpTrackMulti(s, s.tracklist[i], i)

    def ready(s): # send relevant data to DownloadManager
        DLMAN.queue_gp([s.tracklist[s.multi_index]])
        s.wrapper.destroy()

    class GpTrackMulti: # GpTrack subclass that just displays a small line
        def __init__(s, parent, info, my_index):
            s.parent = parent
            s.info = info
            s.my_index = my_index
            s.mainframe = tk.Frame(s.parent.multiframe,bg=COLOR_BUTTON)
            s.titlelabel = tk.Label(s.mainframe,anchor=W,font=FONT_M,bg=COLOR_BUTTON,fg=COLOR_TEXT,width=28,text=info[0])
            s.titlelabel.pack(side=LEFT,padx=(106,0))
            s.artistlabel = tk.Label(s.mainframe,anchor=W,font=FONT_M,bg=COLOR_BUTTON,fg=COLOR_TEXT,width=28,text=info[1])
            s.artistlabel.pack(side=LEFT,padx=(10,0))
            s.albumlabel = tk.Label(s.mainframe,anchor=W,font=FONT_M,bg=COLOR_BUTTON,fg=COLOR_TEXT,width=35,text=info[2])
            s.albumlabel.pack(side=LEFT,padx=(10,0))
            s.btn = tk.Button(s.mainframe,text="S",width=2,relief='ridge',bd=2,bg=COLOR_BUTTON,fg=COLOR_TEXT,activebackground=COLOR_BG_1,activeforeground=COLOR_TEXT,command=s.select)
            s.btn.pack(side=RIGHT,padx=(0,10),pady=2)
            s.mainframe.pack(side=TOP,fill=X,padx=1,pady=(0,1))

        def select(s):
            s.parent.multi_index = s.my_index
            s.parent.generate()

class GpAlbum(GpLine):
    def __init__(s, albumlist):
        GpLine.__init__(s)
        s.albumlist = albumlist
        s.multi_index = 0

        s.generate()

    def __str__(s):
        return "GpAlbum"

    def ready(s): # send relevant data to DownloadManager
        album_tracks = api.get_album_info(s.albumlist[s.multi_index][4])["tracks"]
        DLMAN.queue_gp([OSI.gp_get_track_data(x) for x in album_tracks])
        s.wrapper.destroy()

    def generate(s):
        DlWidget.generate(s) # regenerate mainframe

        '''
            (0) name
            (1) artist
            (2) year
            (3) albumArtRef
            (4) albumId
            (5) explicitType
            (6) query
        '''
        curinfo = s.albumlist[s.multi_index]
        s.image = Image.open(BytesIO(requests.get(curinfo[3]).content))
        s.image = s.image.resize((50,50), Image.ANTIALIAS)
        # get the main color from the image for fancy reasons
        s.bordercolor = color_from_image(s.image)

        if (max(s.bordercolor) + min(s.bordercolor)) / 2 >= 127:
            s.bordercontrast = "#000000"
        else:
            s.bordercontrast = COLOR_TEXT
        s.bordercolor = RGBToHex(s.bordercolor)
        s.typelabel = tk.Label(s.mainframe, bg=s.bordercolor,fg=s.bordercontrast,anchor=CENTER,font=(FONT_M[0], FONT_M[1], 'bold'),width=8,text="Album")
        s.typelabel.pack(side=LEFT,fill=Y)

        s.set_color(s.bordercolor)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe,height=50,width=50,bg=COLOR_BUTTON)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe,anchor=W,image=s.photo,borderwidth=0,highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=28,text=curinfo[0])
        s.titlelabel.pack(side=LEFT,padx=(10,0))
        s.artistlabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=28,text=curinfo[1])
        s.artistlabel.pack(side=LEFT,padx=(10,0))
        s.delbutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="X",width=3,relief='ridge',bd=2,activebackground=COLOR_BG_1,activeforeground=COLOR_TEXT, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=lambda: OSI.dl_delete(s))
        s.delbutton.pack(side=RIGHT,padx=(0,8))
        s.readybutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="OK",width=3,relief='ridge',bd=2,activebackground="green",activeforeground=COLOR_TEXT, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=s.ready)
        s.readybutton.pack(side=RIGHT,padx=(0,8))

        if len(s.albumlist) > 1: # if we actually have alternatives to show, make the multilist
            s.multibutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="ALT",width=5,relief='ridge',bd=2,highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,activebackground=COLOR_BUTTON,activeforeground=COLOR_TEXT,command=s.multipack)
            s.multibutton.pack(side=RIGHT,padx=(0,8))
            s.multiframe = tk.Frame(s.wrapper,bg=s.wrapper.cget("bg")) # indeed not packed, that is done by the multibutton
            for i in range(len(s.albumlist)):
                if i != s.multi_index: # only generate multilines for nonselected tracks
                    s.GpAlbumMulti(s, s.albumlist[i], i)

    class GpAlbumMulti: # GpAlbum subclass that just displays a small line
        def __init__(s, parent, info, my_index):
            s.parent = parent
            s.info = info
            s.my_index = my_index
            s.mainframe = tk.Frame(s.parent.multiframe,bg=COLOR_BUTTON)
            s.titlelabel = tk.Label(s.mainframe,anchor=W,font=FONT_M,bg=COLOR_BUTTON,fg=COLOR_TEXT,width=28,text=info[0])
            s.titlelabel.pack(side=LEFT,padx=(106,0))
            s.artistlabel = tk.Label(s.mainframe,anchor=W,font=FONT_M,bg=COLOR_BUTTON,fg=COLOR_TEXT,width=28,text=info[1])
            s.artistlabel.pack(side=LEFT,padx=(10,0))
            s.btn = tk.Button(s.mainframe,text="S",width=3,relief='ridge',bd=2,bg=COLOR_BUTTON,fg=COLOR_TEXT,activebackground=COLOR_BG_1,activeforeground=COLOR_TEXT,command=s.select)
            s.btn.pack(side=RIGHT,padx=(0,10),pady=2)
            s.mainframe.pack(side=TOP,fill=X,padx=1,pady=(0,1))

        def select(s):
            s.parent.multi_index = s.my_index
            s.parent.generate()

class GpPlaylist(GpLine):
    def __init__(s,tracklist,plinfo):
        GpLine.__init__(s)
        s.plinfo = plinfo
        s.tracklist = tracklist
        s.generate()

    def __str__(s):
        return "GpPlaylist"

    def ready(s): # send relevant data to DownloadManager
        DLMAN.queue_gp(s.tracklist)
        s.wrapper.destroy()

    def generate(s):
        DlWidget.generate(s) # regenerate mainframe

        curinfo = s.plinfo
        s.bordercolor = "#fe5722"
        s.bordercontrast = "#ffffff"
        s.typelabel = tk.Label(s.mainframe, bg=s.bordercolor,fg=s.bordercontrast,anchor=CENTER,font=(FONT_M[0], FONT_M[1], 'bold'),width=8,text="Playlist")
        s.typelabel.pack(side=LEFT,fill=Y)

        s.image = Image.open("etc/gp.png")
        s.image = s.image.resize((50,50), Image.ANTIALIAS)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe,height=50,width=50,bg=COLOR_BUTTON)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe,anchor=W,image=s.photo,borderwidth=0,highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)

        s.set_color(s.bordercolor)
        s.titlelabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=28,text=curinfo[0])
        s.titlelabel.pack(side=LEFT,padx=(10,0))
        s.artistlabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=28,text=curinfo[1])
        s.artistlabel.pack(side=LEFT,padx=(10,0))
        s.albumlabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=12,text=curinfo[2]+" tracks")
        s.albumlabel.pack(side=LEFT,padx=(10,0))
        s.delbutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="X",width=3,relief='ridge',bd=2,activebackground=COLOR_BG_1,activeforeground=COLOR_TEXT, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=lambda: OSI.dl_delete(s))
        s.delbutton.pack(side=RIGHT,padx=(0,8))
        s.readybutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="OK",width=3,relief='ridge',bd=2,activebackground="green",activeforeground=COLOR_TEXT, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=s.ready)
        s.readybutton.pack(side=RIGHT,padx=(0,8))

class YtLine(DlWidget):
    def __init__(s):
        DlWidget.__init__(s)

    def __str__(s):
        return "YtLine (INTERFACE!)"

class YtSingle(YtLine):
    def __init__(s, tracklist):
        YtLine.__init__(s)
        s.tracklist = tracklist
        s.multi_index = 0 # which song to select in the tracklist
        s.generate()

    def __str__(s):
        return "YtSingle"

    def ready(s): # send relevant data to DownloadManager
        DLMAN.queue_yt([s.tracklist[s.multi_index]])
        s.wrapper.destroy()

    def generate(s):
        DlWidget.generate(s) # regenerate mainframe

        DLMAN.generate_image_data(s.tracklist, s.multi_index) # appends image object and primary color to info
        curinfo = s.tracklist[s.multi_index]

        s.bordercolor = curinfo[5]
        s.image = curinfo[4].resize((50,50), Image.ANTIALIAS)
        # get the main color from the image for fancy reasons


        if (max(s.bordercolor) + min(s.bordercolor)) / 2 >= 127:
            s.bordercontrast = "#000000"
        else:
            s.bordercontrast = COLOR_TEXT
        s.bordercolor = RGBToHex(s.bordercolor)
        s.typelabel = tk.Label(s.mainframe, bg=s.bordercolor,fg=s.bordercontrast,anchor=CENTER,font=(FONT_M[0], FONT_M[1], 'bold'),width=8,text="YouTube")
        s.typelabel.pack(side=LEFT,fill=Y)

        s.set_color(s.bordercolor)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe,height=50,width=50,bg=COLOR_BUTTON)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe,anchor=W,image=s.photo,borderwidth=0,highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=90,text=curinfo[0])
        s.titlelabel.pack(side=LEFT,padx=(10,0))
        s.artistlabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=30,text=curinfo[1])
        s.artistlabel.pack(side=LEFT,padx=(10,0))
        s.delbutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="X",width=3,relief='ridge',bd=2,activebackground=COLOR_BG_1,activeforeground=COLOR_TEXT, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=lambda: OSI.dl_delete(s))
        s.delbutton.pack(side=RIGHT,padx=(0,8))
        s.readybutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="OK",width=3,relief='ridge',bd=2,activebackground="green",activeforeground=COLOR_TEXT, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=s.ready)
        s.readybutton.pack(side=RIGHT,padx=(0,8))

        if len(s.tracklist) > 1: # if we actually have alternatives to show, make the multilist
            s.multibutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="ALT",width=5,relief='ridge',bd=2,highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,activebackground=COLOR_BUTTON,activeforeground=COLOR_TEXT,command=s.multipack)
            s.multibutton.pack(side=RIGHT,padx=(0,8))
            s.multiframe = tk.Frame(s.wrapper,bg=s.wrapper.cget("bg")) # indeed not packed, that is done by the multibutton
            for i in range(len(s.tracklist)):
                if i != s.multi_index: # only generate multilines for nonselected tracks
                    s.YtSingleMulti(s, s.tracklist[i], i)

    class YtSingleMulti:
        def __init__(s, parent, info, my_index):
            s.parent = parent
            s.info = info
            s.my_index = my_index
            s.mainframe = tk.Frame(s.parent.multiframe,bg=COLOR_BUTTON)
            s.titlelabel = tk.Label(s.mainframe,anchor=W,font=FONT_M,bg=COLOR_BUTTON,fg=COLOR_TEXT,width=90,text=info[0])
            s.titlelabel.pack(side=LEFT,padx=(106,0))
            s.artistlabel = tk.Label(s.mainframe,anchor=W,font=FONT_M,bg=COLOR_BUTTON,fg=COLOR_TEXT,width=30,text=info[1])
            s.artistlabel.pack(side=LEFT,padx=(10,0))
            s.btn = tk.Button(s.mainframe,text="S",width=2,relief='ridge',bd=2,bg=COLOR_BUTTON,fg=COLOR_TEXT,activebackground=COLOR_BG_1,activeforeground=COLOR_TEXT,command=s.select)
            s.btn.pack(side=RIGHT,padx=(0,10),pady=2)
            s.mainframe.pack(side=TOP,fill=X,padx=1,pady=(0,1))

        def select(s):
            s.parent.multi_index = s.my_index
            s.parent.generate()

class YtMulti(YtLine):
    def __init__(s, tracklist, plinfo):
        YtLine.__init__(s)
        s.tracklist = tracklist
        s.plinfo = plinfo
        s.multi_index = 0 # which song to select in the tracklist
        s.generate()

    def __str__(s):
        return "YtMulti"

    def ready(s):
        DLMAN.queue_yt(s.tracklist)
        s.wrapper.destroy()

    def generate(s):
        DlWidget.generate(s) # regenerate mainframe

        curinfo = s.plinfo
        s.bordercolor = "#fe0000"
        s.bordercontrast = "#ffffff"
        s.typelabel = tk.Label(s.mainframe, bg=s.bordercolor,fg=s.bordercontrast,anchor=CENTER,font=(FONT_M[0], FONT_M[1], 'bold'),width=8,text="Playlist")
        s.typelabel.pack(side=LEFT,fill=Y)

        s.image = Image.open("etc/yt.png")
        s.image = s.image.resize((50,50), Image.ANTIALIAS)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe,height=50,width=50,bg=COLOR_BUTTON)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe,anchor=W,image=s.photo,borderwidth=0,highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)

        s.set_color(s.bordercolor)
        s.titlelabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=28,text=curinfo[0])
        s.titlelabel.pack(side=LEFT,padx=(10,0))
        s.artistlabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=28,text=curinfo[1])
        s.artistlabel.pack(side=LEFT,padx=(10,0))
        s.albumlabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=12,text=str(curinfo[2])+" tracks")
        s.albumlabel.pack(side=LEFT,padx=(10,0))
        s.delbutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="X",width=3,relief='ridge',bd=2,activebackground=COLOR_BG_1,activeforeground=COLOR_TEXT, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=lambda: OSI.dl_delete(s))
        s.delbutton.pack(side=RIGHT,padx=(0,8))
        s.readybutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="OK",width=3,relief='ridge',bd=2,activebackground="green",activeforeground=COLOR_TEXT, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=s.ready)
        s.readybutton.pack(side=RIGHT,padx=(0,8))

class StWidget:
    def __init__(s,key,label,col,row,type,altkey=None): # internal settings key, label for user, column in stframe, row in stframe, type of setting (text, bool, file, folder)
        s.key = key
        s.altkey = altkey
        s.type = type
        s.mainframe = tk.Frame(OSI.stframe,bg=COLOR_BUTTON,width=300,height=20,bd=0,highlightbackground=COLOR_BG_3,highlightcolor=COLOR_BG_3,highlightthickness=2)
        s.mainframe.grid(column=col,row=row)
        s.label = tk.Label(s.mainframe, bg=COLOR_BUTTON,fg=COLOR_TEXT,text=label, font=FONT_M,width=60)
        s.label.grid(column=0,row=0)
        if type != "bool":
            s.curlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON,fg=COLOR_TEXT,text=settings[key],font=FONT_ITALIC,width=60)
            s.curlabel.grid(column=0,row=1)
        if type in ["file","folder"]:
            s.changebutton = tk.Button(s.mainframe,text="CHANGE", bg=COLOR_BUTTON,activeforeground=COLOR_TEXT,activebackground=COLOR_BG_3,width=10,fg=COLOR_TEXT,border=0,font=FONT_M,command=lambda: OSI.promptSetting(key,type))
            s.changebutton.grid(column=1,row=0,rowspan=2,sticky="NESW")
        elif type == "bool":
            s.switchbutton = tk.Button(s.mainframe,text=settings[key], bg=COLOR_BUTTON,width=10,activeforeground=COLOR_TEXT,activebackground=COLOR_BG_3,fg=COLOR_TEXT,border=0,font=FONT_M,command=lambda: OSI.switchSetting(key))
            s.switchbutton.grid(column=1,row=0)
        elif type == "list":
            s.nextbutton = tk.Button(s.mainframe, text="SWITCH", bg=COLOR_BUTTON,activeforeground=COLOR_TEXT,activebackground=COLOR_BG_3,width=10,fg=COLOR_TEXT,border=0,font=FONT_M,command=None)
            s.nextbutton.configure(command=lambda: [OSI.cycleSetting(key,altkey)])
            # list should include a method that does something with the setting
            # some setter, for example
            s.nextbutton.grid(column=1,row=0, rowspan=2,sticky="NESW")

        s.mainframe.grid(column=col,row=row,pady=8,padx=8)

    def update(s):
        if s.type != "bool":
            s.curlabel.configure(text=settings[s.key])
        else:
            s.switchbutton.configure(text=settings[s.key])


class dbLine: # !!! move to below music classes when done
    def __init__(s,path, indx):
        s.isfile = path.endswith((".txt",".aegis"))
        s.isaegis = path.endswith(".aegis")
        s.indexval = indx
        # if not s.isfile:
        #     s.indexval = dbstate[2].index(path)
        # else:
        #     if not s.isaegis or not openable: s.indexval = dbstate[1].index(path)+len(dbstate[2])
        #     else:
        #         if openable: s.indexval = dbstate[4].index(display) + len(dbstate[2])


        s.wrapper = tk.Frame(OSI.dbframe,height=25, bg=COLOR_BG_3)
        s.wrapper.pack_propagate(0)
        s.mainframe = tk.Frame(s.wrapper,bg=COLOR_BUTTON)
        s.indexlabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=3,text=('00'+str(s.indexval+1))[-2:])
        s.indexlabel.pack(side=LEFT,padx=(10,0))
        s.typelabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=10)
        s.typelabel.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,anchor=W,font=FONT_M,width=28)
        s.titlelabel.pack(side=LEFT,padx=(10,0))
        if dbstate[3][s.indexval] == "aeg_nokey":
            s.titlelabel.configure(text="-- KEY REQUIRED --")
        elif dbstate[3][s.indexval] == "aeg_wrongkey":
            s.titlelabel.configure(text="-- INCORRECT KEY --")
        else:
            s.titlelabel.configure(text=dbstate[1][s.indexval])
        #     if s.isfile: s.titlelabel.configure(text=".".join(path.split("\\")[-1].split(".")[:-1]))
        #     else: s.titlelabel.configure(text=path.split("\\")[-1])
        # else: s.titlelabel.configure(text=display)
        if s.isfile:
            if s.isaegis: s.typelabel.configure(text="AEGIS")
            else: s.typelabel.configure(text="TEXT")
            s.delbutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="DEL",width=6,relief='ridge',bd=0,activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT, command=lambda: OSI.dbinterpret("d "+str(s.indexval+1)))
            s.delbutton.pack(side=RIGHT)
        else:
            s.typelabel.configure(text="FOLDER")
        if dbstate[3][s.indexval] not in ["aeg_nokey","aeg_wrongkey"]:
            s.openbutton = tk.Button(s.mainframe,bg=COLOR_BUTTON,fg=COLOR_TEXT,font=FONT_M,text="OPEN",width=6,relief='ridge',bd=0,activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT, command=lambda: OSI.dbinterpret("o "+str(s.indexval+1)))
            s.openbutton.pack(side=RIGHT)
        s.mainframe.pack(side=TOP,fill=X,padx=1,pady=1)
        s.wrapper.pack(side=TOP,pady=(2,0),padx=10,fill=X)

class GpLineEmpty: # !!! move to below music classes when done
    def __init__(s,query):
        s.mainframe = tk.Frame(OSI.dlframe,highlightthickness=2,highlightbackground="white")
        s.emptylabel = tk.Label(s.mainframe,fg="#c41313",text=("NO MATCH: "+query))
        s.emptylabel.pack(side=TOP)
        s.mainframe.pack(side=TOP,pady=(10,0),padx=10,fill=X)
        root.after(3000,s.remove)
    def remove(s):
        s.mainframe.pack_forget()
        s.mainframe.destroy()

class pliLine:
    def __init__(s,info):
        s.info = info
        s.plisframe = tk.Frame(OSI.pliframe,width=260,height=20, bg=COLOR_BG_2)
        s.plisframe.pack_propagate(0)
        s.plitextstring = (s.info[0]+" "*10)[:10]+" "+(s.info[1]+" "*3)[:3]+" "+(s.info[2]+" "*3)[:3]
        if settings["set_pliduration"]=="True":
            s.plitextstring += " "+(s.info[3]+" "*5)[:5]
        s.plitext = tk.Label(s.plisframe,font=FONT_M,text=s.plitextstring,bg=COLOR_BG_2,fg=COLOR_TEXT)
        s.plitext.pack(side=LEFT,anchor=W)
        s.pliplaybtn = tk.Button(s.plisframe,font=FONT_M,pady=0,borderwidth=0,text="P",bg=COLOR_BG_1,fg=COLOR_TEXT,command=lambda:OSI.mpinterpret("pl "+s.info[0]))
        s.pliloadbtn = tk.Button(s.plisframe,font=FONT_M,pady=0,borderwidth=0,text="L",bg=COLOR_BG_1,fg=COLOR_TEXT,command=lambda:OSI.mpinterpret("pll "+s.info[0]))
        s.plisavebtn = tk.Button(s.plisframe,font=FONT_M,pady=0,borderwidth=0,text="S",bg=COLOR_BG_1,fg=COLOR_TEXT,command=lambda:OSI.mpinterpret("plsave "+s.info[0]))
        s.plisavebtn.pack(side=RIGHT,anchor=W)
        s.pliloadbtn.pack(side=RIGHT,anchor=W)
        s.pliplaybtn.pack(side=RIGHT,anchor=W)
        s.plisframe.pack(side=TOP,fill=X,pady=1)

class MpWidget:
    def __init__(s,path):
        s.path = path
        musicPaths.append(s.path)
        s.index = musicPaths.index(s.path)

        # first, getting data from path
        temp = s.path.split("\\")[-3:]
        s.title_name = temp[-1][:-4]
        if is_int(s.title_name.split()[0]):
            s.title_name = " ".join(s.title_name.split()[1:])
        s.artist_name = temp[-3]
        s.album_name = temp[-2]

        # defining single song widget layout
        s.mainframe = tk.Frame(OSI.mpframe,highlightthickness=0,width=TK_WIDTH-20,height=28,bd=0)
        s.mainframe.pack_propagate(0)
        s.indexlabel = tk.Label(s.mainframe,font=FONT_M,fg=COLOR_TEXT,width=4,anchor=W,text=(("000"+str(int(s.index)+1))[-3:]))
        s.indexlabel.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe,font=FONT_M,fg=COLOR_TEXT,width=45,anchor=W, text=s.title_name)
        s.titlelabel.pack(side=LEFT,padx=(0,15))
        s.artistlabel = tk.Label(s.mainframe,font=FONT_M,fg=COLOR_TEXT,width=30,anchor=W,text=s.artist_name)
        s.artistlabel.pack(side=LEFT,padx=(0,15))
        s.albumlabel = tk.Label(s.mainframe,font=FONT_M,fg=COLOR_TEXT,width=40,anchor=W,text=s.album_name)
        s.albumlabel.pack(side=LEFT)
        s.buttonframe = tk.Frame(s.mainframe,highlightthickness=0,bd=0,width=60,height=s.mainframe.cget("height"))
        s.buttonframe.pack_propagate(0)
        s.destroybutton = tk.Button(s.buttonframe,font=FONT_M,bg=COLOR_BG_3,fg=COLOR_TEXT,command=s.remove,text="X",width=2,relief="flat")
        s.destroybutton.pack(side=RIGHT,pady=(0,0))
        s.playbutton = tk.Button(s.buttonframe,font=FONT_M,bg=COLOR_BG_3,fg=COLOR_TEXT,command=lambda:OSI.mpplay([s.path]),text="P",width=2,relief="flat")
        s.playbutton.pack(side=RIGHT,padx=(0,0),pady=(0,0))
        s.buttonframe.pack(side=RIGHT,pady=(0,0))

        s.widgetlist = [s.mainframe,s.indexlabel,s.titlelabel,s.artistlabel,s.albumlabel,s.buttonframe]
        s.altlist = [s.destroybutton,s.playbutton]
        if int(s.index%2==0):
            for i in s.widgetlist:i.configure(bg=COLOR_BG_2)
            #for i in s.altlist:i.configure(bg=COLOR_BG_1)
        else:
            for i in s.widgetlist:i.configure(bg=COLOR_BG_1)
            #for i in s.altlist:i.configure(bg=COLOR_BG_2)

    def show(s):
        s.mainframe.pack(side=TOP,fill=X)

    def hide(s):
        if s.mainframe.winfo_ismapped():
            s.mainframe.pack_forget()

    def update(s):
        temp = str(s.index)[:]
        s.index = mpWidgets.index(s)
        if temp != s.index:
            s.indexlabel.configure(text=(("00"+str(int(s.index)+1))[-2:]))
            if int(s.index%2==0):
                for i in s.widgetlist:i.configure(background=COLOR_BG_2)
            else:
                for i in s.widgetlist:i.configure(background=COLOR_BG_1)

    def remove(s, mass_remove=False): # on mass remove, it is assumed that updating tasks will be performed afterwards, so OSI.mpupdate need not be called
        s.update()
        del musicPaths[s.index]
        s.mainframe.destroy()
        del mpWidgets[s.index]
        if not(mass_remove):
            OSI.mpupdate()


# LAUNCH PREP
root = tk.Tk()
OSI = MainUI(root)
DLMAN = DownloadManager()
OSI.greet()

# root operations first

if settings["set_notitle"]=="True":
    OSI.buttonframe.bind('<B1-Motion>', move_window)
    OSI.buttonframe.bind('<Button-1>', def_delta)
    root.overrideredirect(True)
    geomheight = str(TK_HEIGHT)#+70)
    geomwidth = str(TK_WIDTH)#+312)
    root.geometry(geomwidth+"x"+geomheight+"+0+0")

if settings["set_update"]=="True":
    foobarprev = ""
    root.after(0,update)

root.iconbitmap("etc/osi.ico")

if settings["set_showscrollbar"]=="True":
    root.after(50,lambda : OSI.scrollcanvas.config(scrollregion=OSI.scrollcanvas.bbox("all")))

OSI.rootframe.bind("<FocusIn>",lambda x: OSI.attemptMaximise())
root.bind("<Alt-v>",lambda x: OSI.attemptMinimise())

# OSI operations
bindlist = [root,OSI.glbentry,OSI.dbeditor,OSI.dbtitle]
for i in bindlist:
    i.bind("[",OSI.tableft)
    i.bind("]",OSI.tabright)

# mp

OSI.mp_pageHandler = PageHandler("mp",MP_PAGE_SIZE)

OSI.mprefresh()

# db
OSI.glbentry.bind("<Key>", lambda x: root.after(10,OSI.responsive))
OSI.dbtitle.bind("<Tab>", OSI.dbfocusedit)
OSI.glbentry.bind("<Tab>", OSI.dbfocusedit)
OSI.dbeditor.bind("<Tab>", OSI.dbfocusentry)

OSI.dbrefresh()

OSI.log("OSI: MP and DB loaded")

api = None # this is imported asynchronously due to long delay (.6 seconds)
webapi = None
gplogin = False
gppass = settings["gppass"]
threading.Thread(target=OSI.gpbackgroundlogin).start()

# settings
OSI.StWidgets = [StWidget("searchdir","Music folder",0,0,"folder"),
                StWidget("dldir","Download folder",0,1,"folder"),
                StWidget("foobarexe","Foobar EXE",0,2,"file"),
                StWidget("set_notitle","Use own title bar instead of windows",0,3,"bool"),
                StWidget("set_pliduration","Show lengths of playlists in 'pli' menu",0,4,"bool"),
                StWidget("set_update","Get updates from foobar",0,5,"bool"),
                StWidget("set_foobarplaying","Show currently playing song",0,6,"bool"),
                StWidget("set_draggable","Make window draggable with mouse",0,7,"bool")]

get_attention(root)
root.mainloop()
