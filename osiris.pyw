# Continuation of the first tkinter shell, nicknamed Osiris
# note that 's.' was used instead of 'self.' because I am an ungodly bastard
# and / or because I am lazy
#
# - RFK 2018 -

# built-in libraries
import time
starting_time = time.time()
def t_since_start(): print(time.time() - starting_time) # call this anywhere to check delays in startup time

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
def importSettings(path="etc/settings.txt"):
    global settings
    settings = {}
    settingsfile = open(path,"r")
    for i in settingsfile:
        (key,value) = i.split(" = ")
        value = value.rstrip("\n")
        settings[key] = value
    settingsfile.close()

def exportSettings(path="etc/settings.txt"):
    settingsfile = open(path,"w")
    for key,value in settings.items():
        settingsfile.write(key+" = "+value+"\n")
    settingsfile.close()

importSettings()

# LOCAL SETTINGS
# tkinter settings
fontset = ("Roboto Mono", "10")  # font name + size
fontset2 = ("Roboto Mono", "11")
smallfont = ("Roboto Mono", "8")
italicfont = ("Roboto Mono", "10", "italic")
boldfont = ("Roboto Mono", "11", "bold")
tkheight = 1030
tkwidth = 1920
tkpadding = 10
tklogheight = 40 # 25 under height 600
tkbuttonwidth = 27

# tkinter A E S T H E T I C
tkbgcolor = "#2e3338" #"#282C30"
tkbgcolor2 = "#394046" # secondary music selection color
tkbgcolor3 = "#454d54" # music selection button color

tkbuttoncolor = "#14161A"
tkbuttoncoloract = tkbgcolor
tktxtcol = "#D3D7DE"
tkentrytextcolor = tktxtcol
tkbuttontextcolor = tktxtcol
tkbuttontextcoloract = tktxtcol

# db settings
dbdir = "database/"
enclevel = 3 # depth of Aegis AES-256 ecryption

# gp settings
DL_ALTERNATIVES = 5


# setup
if not os.path.exists(dbdir):
    os.mkdir(dbdir)
musicWidgets = []
musicPaths = []
allfiles = []
dbloc = dbdir
dbstate = ["browse",[],[],[]] # mode, showlist, pathlist, maplist
dbkey = False
dbWidgets = []
dlWidgets = [] # list of instantiations of dlLine (or derived classes)
wkWidgets = []

# make gmusicapi shut up
logging.disable(logging.CRITICAL)

# Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn
# seriously, I don't even know, just don't touch
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

def getattention(root):
    root.lift()
    root.attributes("-topmost", True)
    root.attributes("-topmost", False)
    root.after(10,lambda: set_appwindow(root))
    root.after(200,lambda: root.focus_force())
    root.after(300,lambda: OSI.glbentry.focus())

mousex, mousey = 0,0
def def_delta(event):
    global mousex, mousey
    mousex = event.x
    mousey = event.y

def move_window(event):
    root.geometry("+"+str(event.x_root-mousex)+"+"+str(event.y_root-mousey))

# TOPLEVEL UTILITY DEFS
def search(find,total): # quicksearch, as there is no option for recursive selection due to tkinter not wanting to wait for input
    find = find.split(";") # ["foo bar", "tra la"]
    results = []
    for term in find: # term = "foo bar", "tra la"
        term = term.split()
        remlist = []
        for single in term:
            if single.startswith("-"):
                remlist.append(single[1:])
        for full in total: # loops through every entry in the total list
            match = True
            for single in term: # single = "foo"
                if not single.startswith("-"):
                    if single.lower() not in full.lower(): match = False
            if match:
                for rem in remlist:
                    if rem.lower() in full.lower(): match = False
                if match and full not in results:
                    results.append(full)
    return results

def matchcrit(crit, searchlist, shift = 0): # interprets search criteria
    match = [] #list of all files that match criteria given
    for i in crit.split(";"):
        if len(i.split("-"))==2:
            if isint(i.split("-")[0]) and isint(i.split("-")[1]):
                # criterium is range of files
                match += searchlist[int(i.split("-")[0])-shift-1:int(i.split("-")[1])-shift]
        if isint(i):
            # criterium is single file
            if int(i)-shift <= len(searchlist):
                match += [searchlist[int(i)-shift-1]]
        else:
            # criterium is string to search
            match += search(i,searchlist)
    return match

def isint(val): # checks whether a value can be converted to an integer
    try:
        int(val)
        return True
    except:
        return False

def dupl_rem(duplist): # function to remove duplicate values from a list
    seen = set()
    seen_add = seen.add
    return [x for x in duplist if not (x in seen or seen_add(x))]

def filterchars(string_in,chars):
    out = "".join(list(filter(lambda x: x not in chars, list(string_in))))
    return out

def escape(string): # escape backslashes
    val = repr(string)
    for i in range(4):
        val = val.replace([r"\x0",r"\n",r"\l",r"\t"][i],
                          [r"\\0",r"\\n",r"\\l",r"\\t"][i])
    return val.strip("'")

def fltr(string):
    temp = string[:]
    changelist = '*/\\":?<>|'
    for i in range(3):
        for char in changelist:
            temp = temp.replace(char,"_")
    return temp


# TOPLEVEL TEXT INTERACTION DEFS
def selectFile(filepath=settings["datapath"]): # function used by all 'text' functions to get the content of osData.txt, also applicable for other .txt files
    with open(filepath,"r") as selectedFile:
        data = [x.strip('\n') for x in selectedFile.readlines()]
    return data

def writeToText(writeList,section): # replaces the current content of section with that of writeList, creates section if there is none
    data = selectFile()
    try:
        dataStartIndex = data.index("="+section+"=")+1
        dataEndIndex = data.index("=/"+section+"=")
    except:
        data += ["="+section+"="] + ["=/"+section+"="]
        dataStartIndex = data.index("="+section+"=")+1
        dataEndIndex = data.index("=/"+section+"=")
    data[dataStartIndex:dataEndIndex] = []
    for i in writeList[::-1]:
        data.insert(dataStartIndex,i)
    dataWriteFile = open(settings["datapath"],"w")
    for i in data:
        dataWriteFile.write(str(i)+"\n")
    dataWriteFile.close()

def readFromText(section): # gets the content of a section
    data = selectFile()
    try:
        dataStartIndex = data.index("="+section+"=")+1
        dataEndIndex = data.index("=/"+section+"=")
    except: return False
    return(data[dataStartIndex:dataEndIndex])

def delText(section): # deletes a section
    data = selectFile()
    try: data[(data.index("="+section+"=")):(data.index("=/"+section+"=")+1)] = []
    except: return False
    dataWriteFile = open(settings["datapath"],"w")
    for i in data: dataWriteFile.write(i+"\n")
    dataWriteFile.close()
    return True

def searchText(section): # returns the names of all matching sections
    data = selectFile()
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
        foobarnow = [open("foobar_nowplaying.txt","r").readlines()][0][0].rstrip("\n")[3:]
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

                colors = image.getcolors(2500)
                max_occurence, most_present = 0, 0
                for c in colors:
                    if c[0] > max_occurence:
                        (max_occurence, most_present) = c

                bordercolor = ("#"+('00'+str(hex(most_present[0]))[2:])[-2:]+('00'+str(hex(most_present[1]))[2:])[-2:]+('00'+str(hex(most_present[2]))[2:])[-2:])
                s.mpfoobarwrapper.configure(bg=bordercolor)

                temp = foobarnow.lstrip("playing: ").split("\\")
                OSI.mpfoobartext.configure(text="Song:   "+temp[-1][3:-4]+"\nArtist: "+temp[-3]+"\nAlbum:  "+temp[-2])
                foobarprev = foobarnow[:]
        root.after(1000,update)
    except:
        root.after(1000,update)


# MAIN WINDOW DEFINITION
class mainUI:
    def __init__(s,master):
        # some pre-op (can be anywhere in this init)
        s.pliactive = False
        s.entryhist = ['']
        s.entrypos = 0
        s.state = "max"

        # start of window definition and setup
        s.master = master
        master.title("Osiris")
        master.resizable(0,0)
        s.rootframe = tk.Frame(s.master,background=tkbuttoncolor)

        s.mainframe = tk.Frame(s.rootframe,bg=tkbuttoncolor)

        # time for the bulk of the widgets
        s.buttonframe = tk.Frame(s.mainframe,bg=tkbuttoncolor,height=38)
        s.buttonframe.pack_propagate(0)



        # adding logo
        s.logoframe = tk.Frame(s.buttonframe, height=38, width=80,bg=tkbuttoncolor)
        s.logoframe.pack_propagate(0)
        s.logoimage = Image.open("etc/background-white-logo.png")
        s.logoimage = s.logoimage.resize((57,30),Image.ANTIALIAS)
        s.logophoto = ImageTk.PhotoImage(s.logoimage)
        s.logolabel = tk.Label(s.logoframe, height=33, width=66, image=s.logophoto,bg=tkbuttoncolor)
        s.logolabel.image = s.logophoto
        s.logolabel.pack(padx=10,pady=4)
        s.logoframe.pack(side=LEFT)

        s.mpbutton = tk.Button(s.buttonframe,borderwidth=0,activebackground=tkbuttoncoloract,activeforeground=tktxtcol,font=fontset2,width=tkbuttonwidth,text="MUSIC",command=lambda:s.select("mp"))
        s.dbbutton = tk.Button(s.buttonframe,borderwidth=0,activebackground=tkbuttoncoloract,activeforeground=tktxtcol,font=fontset2,width=tkbuttonwidth,text="DATABASE",command=lambda:s.select("db"))
        s.dlbutton = tk.Button(s.buttonframe,borderwidth=0,activebackground=tkbuttoncoloract,activeforeground=tktxtcol,font=fontset2,width=tkbuttonwidth,text="DOWNLOAD",command=lambda:s.select("dl"))
        s.wkbutton = tk.Button(s.buttonframe,borderwidth=0,activebackground=tkbuttoncoloract,activeforeground=tktxtcol,font=fontset2,width=tkbuttonwidth,text="WORK",command=lambda:s.select("wk"))
        s.stbutton = tk.Button(s.buttonframe,borderwidth=0,activebackground=tkbuttoncoloract,activeforeground=tktxtcol,font=fontset2,width=tkbuttonwidth,text="SETTINGS",command=lambda:s.select("st"))
        # list of buttons
        s.buttonw = [s.mpbutton,s.dbbutton,s.dlbutton,s.wkbutton,s.stbutton]

        for i in s.buttonw:
            i.pack(side=LEFT, fill=Y)

        if settings["set_notitle"]=="True":
            s.exitbutton = tk.Button(s.buttonframe,borderwidth=0,bg=tkbuttoncolor,activebackground="#c41313",fg=tktxtcol,activeforeground="white",font=boldfont,width=4,text=" X ",command=root.destroy)
            s.exitbutton.bind("<Enter>", lambda x: s.exitbutton.configure(bg="#c41313"))
            s.exitbutton.bind("<Leave>", lambda x: s.exitbutton.configure(bg=tkbuttoncolor))
            s.exitbutton.pack(side=RIGHT)
            # minimize not possible because of overrideredirect
            s.minbutton = tk.Button(s.buttonframe,borderwidth=0,bg=tkbuttoncolor,activebackground=tkbgcolor3,fg=tktxtcol,activeforeground="white",font=boldfont,width=4,text=" _ ",command=s.attemptMinimise)
            s.minbutton.bind("<Enter>", lambda x: s.minbutton.configure(bg=tkbgcolor3))
            s.minbutton.bind("<Leave>", lambda x: s.minbutton.configure(bg=tkbuttoncolor))
            s.minbutton.pack(side=RIGHT)
        s.buttonframe.grid(column=0,columnspan=2,row=0,sticky=W+E)

        # the sandwich goes:
        #  contentwrapperframe
        #   scrollcanvas
        #    contentframe
        #     ALL FRAME WIDGETS (mp, db, dl)
        s.contentwrapperframe = tk.Frame(s.mainframe,bg=tkbgcolor,height=tkheight-64,width=tkwidth-306)
        s.scrollcanvas = tk.Canvas(s.contentwrapperframe,bg=tkbgcolor,yscrollincrement="1")
        s.scrollcanvas.pack(side=LEFT,fill=BOTH,expand=True)

        if settings["set_showscrollbar"]=="True":
            s.scrollbar = tk.Scrollbar(s.contentwrapperframe, command=s.scrollcanvas.yview)
            s.scrollbar.pack(side=RIGHT, fill=Y)
            s.scrollcanvas.config(yscrollcommand=s.scrollbar.set)

        s.contentframe = tk.Frame(s.scrollcanvas,bg=tkbgcolor)

        # s.contentframe.pack_propagate(0)
        if settings["set_scrollable"]=="False":
            s.contentframe.pack(fill=BOTH,expand=True)

        if settings["set_scrollable"]=="True":
            s.scrollcanvas.create_window(0,0,window=s.contentframe,anchor="nw")
            s.scrollcanvas.bind_all("<MouseWheel>", s.mousewheel)

        s.logoimage = Image.open("etc/osi.png")

        s.mpframe = tk.Frame(s.contentframe,bg=tkbgcolor)

        if settings["set_foobarplaying"]=="True":
            s.mpfoobarwrapper = tk.Frame(s.mpframe,bg=tkbuttoncolor)
            s.mpfoobarwrapper.place(y=450,height=100,width=400)
            s.mpfoobarframe = tk.Frame(s.mpfoobarwrapper,bg=tkbgcolor)
            s.mpfoobaralbart = tk.Label(s.mpfoobarframe,bg=tkbgcolor)
            s.mpfoobaralbart.place(height=100,width=100)
            s.mpfoobartext = tk.Label(s.mpfoobarframe,text="",fg=tktxtcol,bg=tkbgcolor)
            s.mpfoobartext.place(x=105)
            s.mpfoobarplaypause = tk.Label(s.mpfoobarframe,text="",fg=tktxtcol,bg=tkbgcolor)
            s.mpfoobarplaypause.place(x=340,y=70)
            s.mpfoobarframe.pack(side=TOP,pady=2,padx=2,fill=BOTH,expand=True)

        s.glbentry = tk.Entry(s.mainframe,font=fontset2,bg=tkbuttoncolor,fg=tkentrytextcolor,borderwidth=0,insertbackground=tkentrytextcolor)
        s.glbentry.bind("<Return>",lambda x:s.visentry(s.glbentry.get()))
        s.glbentry.bind("<Up>",lambda x:s.entrymove("up"))
        s.glbentry.bind("<Down>",lambda x:s.entrymove("down"))
        s.glbentry.grid(column= 0 , row = 2, sticky=W+E)
        s.glbentry.focus()

        s.dbframe = tk.Frame(s.contentframe,background=tkbgcolor)
        s.dbinfoframe = tk.Frame(s.dbframe)
        s.dbloclabel = tk.Label(s.dbinfoframe,bg=tkbgcolor, fg=tktxtcol, font=fontset, text="Browsing: "+dbloc)
        s.dbloclabel.pack(side=LEFT)
        s.dbinfoframe.pack(side=TOP)
        s.dbeditorframe = tk.Frame(s.dbframe,bg=tkbuttoncolor,highlightthickness=2,highlightbackground=tkbgcolor3,highlightcolor=tkbgcolor3,relief="flat")
        s.dbtitlewrapper = tk.Frame(s.dbeditorframe, bg=tkbgcolor3)
        s.dbtitle = tk.Text(s.dbtitlewrapper,height=1,bd=0,font=(fontset[0],14),bg=tkbuttoncolor,insertbackground=tktxtcol,fg=tktxtcol)
        s.dbtitle.pack(fill=X,pady=(0,2),padx=10)
        s.dbtitlewrapper.pack(fill=X)
        s.dbeditor = tk.Text(s.dbeditorframe,height=tklogheight,font=fontset,bg=tkbuttoncolor,bd=0,insertbackground=tktxtcol,fg=tktxtcol,wrap="word")
        s.dbeditor.pack(padx=10,pady=5, fill=BOTH)

        # s.dbloadreq = tk.Label(s.dbframe,bg=tkbuttoncolor,fg=tktxtcol,font=(fontset[0],"25"),text="ENTER TO LOAD DATABASE")
        # s.dbloadreq.pack(side=TOP,fill=BOTH,expand=True,padx=10,pady=10)

        s.dlframe = tk.Frame(s.contentframe,background=tkbgcolor)
        s.dlloginreq = tk.Label(s.dlframe,bg=tkbuttoncolor,fg=tktxtcol,font=(fontset[0],"25"),text="LOGGING IN, PLEASE WAIT")
        s.dlloginreq.pack(side=TOP,fill=BOTH,expand=True,padx=10,pady=10)

        s.wkframe = tk.Frame(s.contentframe,background=tkbuttoncolor)
        s.wkframe.grid_propagate(0)
        for i in range(2): s.wkframe.grid_columnconfigure(i,minsize=int(tkwidth/2)-tkpadding)
        s.wkframe.grid_rowconfigure(0,minsize=int(tkheight/2))
        s.wktodos = tk.Frame(s.wkframe,bg=tkbuttoncolor,width=tkwidth-2*tkpadding)
        s.wktodos.grid(column=0,row=0,columnspan=2,sticky="NESW",padx=2)
        s.wktodos.grid_rowconfigure(1,minsize=int(tkheight/2)-28)
        for i in range(3): s.wktodos.grid_columnconfigure(i,minsize=int((tkwidth-2*tkpadding)/3)-1)
        s.wktodolbl1 = tk.Label(s.wktodos,font=fontset,text="TODO",fg=tktxtcol,bg=tkbuttoncolor)
        s.wktodolbl1.grid(column=0,row=0,sticky="NESW",padx=(0,1))
        s.wktodolbl2 = tk.Label(s.wktodos,font=fontset,text="IN PROGRESS",fg=tktxtcol,bg=tkbuttoncolor)
        s.wktodolbl2.grid(column=1,row=0,sticky="NESW",padx=1)
        s.wktodolbl3 = tk.Label(s.wktodos,font=fontset,text="DONE",fg=tktxtcol,bg=tkbuttoncolor)
        s.wktodolbl3.grid(column=2,row=0,sticky="NESW",padx=(0,1))
        s.wktodolist1 = tk.Frame(s.wktodos,bg=tkbgcolor)
        s.wktodolist1.grid(column=0,row=1,sticky="NESW")
        s.wktodolist2 = tk.Frame(s.wktodos,bg=tkbgcolor)
        s.wktodolist2.grid(column=1,row=1,padx=2,sticky="NESW")
        s.wktodolist3 = tk.Frame(s.wktodos,bg=tkbgcolor)
        s.wktodolist3.grid(column=2,row=1,sticky="NESW")
        s.wkadd1 = tk.Button(s.wktodolist1,text="+",width=2,font=smallfont,bg=tkbuttoncolor,fg=tktxtcol,command=lambda: wkWidgets.append(wkLine("test1",0)))
        s.wkadd2 = tk.Button(s.wktodolist2,text="+",width=2,font=smallfont,bg=tkbuttoncolor,fg=tktxtcol,command=lambda: wkWidgets.append(wkLine("test2",1)))
        s.wkadd3 = tk.Button(s.wktodolist3,text="+",width=2,font=smallfont,bg=tkbuttoncolor,fg=tktxtcol,command=lambda: wkWidgets.append(wkLine("test3",2)))
        for i in [s.wkadd1,s.wkadd2,s.wkadd3]:
            i.pack(side=BOTTOM)
        s.wkassoctextframe = tk.Frame(s.wkframe)
        s.wkassoctextframe.grid(column=0,row=1)
        s.wkassoctext = tk.Text(s.wkassoctextframe,font=fontset,width=60,bg=tkbgcolor2,bd=0,insertbackground=tktxtcol,fg=tktxtcol,wrap="word")
        s.wkassoctext.pack()
        s.wkgentextframe = tk.Frame(s.wkframe)
        s.wkgentextframe.grid(column=1,row=1)
        s.wkgentext = tk.Text(s.wkgentextframe,font=fontset,width=60,bg=tkbgcolor2,bd=0,insertbackground=tktxtcol,fg=tktxtcol,wrap="word")
        s.wkgentext.pack()

        s.stframe = tk.Frame(s.contentframe,background=tkbgcolor)
        # key,label,col,row,type




        # one final thing: the log
        s.logframe = tk.Frame(s.mainframe,width=300,bg=tkbgcolor)
        s.loglabel = tk.Label(s.logframe,text="",font=fontset2,height=tklogheight,bg=tkbgcolor,fg=tktxtcol,anchor=W,justify=LEFT) #"SystemButtonFace",text="BAAAAH")
        s.loglabel.pack(pady=(0,2),fill=X,side=BOTTOM)

        s.logframe.grid(column=1,row=1,sticky="NESW",padx=(6,0),pady=0)
        s.logframe.pack_propagate(0)

        s.responsiveframe = tk.Frame(s.mainframe,height=26,width=300,bg=tkbuttoncolor)
        s.responsiveframe.pack_propagate(0)
        s.responsivelabel = tk.Label(s.responsiveframe,text="",height=1,font=fontset2,bg=tkbuttoncolor,fg="white")
        s.responsivelabel.pack(side=LEFT)
        s.responsiveframe.grid(column=1,row=2,sticky=E)
        # main window definitions complete, now doing pre-op on the widgets
        # list of modes for convenience

        # lists of things
        s.modes = ["mp","db","dl","wk","st"]
        s.frames = [s.mpframe,s.dbframe,s.dlframe,s.wkframe,s.stframe]
        s.interpreters = [s.mpinterpret,s.dbinterpret,s.dlinterpret,s.wkinterpret,s.stinterpret]

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
        #     s.background = tk.Label(i, image=s.backgroundphoto, bg=tkbgcolor)
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
        newlog = (int(tklogheight)*[""]+oldlog.split("\n")+[str(tolog)])[-1*int(tklogheight):]
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
        for i in s.buttonw: i.configure(relief=RAISED,bg=tkbuttoncolor,fg=tktxtcol)

        # selecting the mode to switch to and applying appropriate widget changes
        s.modeindex = s.modes.index(choice)

        s.buttonw[s.modeindex].configure(relief=SUNKEN,bg=tkbuttoncoloract,fg=tktxtcol)
        s.frames[s.modeindex].pack(fill=BOTH,expand=True,pady=tkpadding,padx=tkpadding)
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
                    msg = "Select " + str(len(matchcrit(comm,allfiles))) + " song(s)"
                if flag == "p":
                    if musicPaths == []:
                        msg = "Play " + str(len(matchcrit(comm,allfiles))) + " song(s)"
                    else:
                        msg = "Play " + str(len(matchcrit(comm,musicPaths))) + " song(s)"
                if flag == "r":
                    msg = "Refine to " + str(len(matchcrit(comm,musicPaths))) + " song(s)"
                if flag == "d":
                    msg = "Remove " + str(len(matchcrit(comm,musicPaths))) + " song(s)"
                if flag == "bin":
                    msg = "Send " + str(len(matchcrit(comm,musicPaths))) + " song(s) to trash"
                if flag == "gp":
                    if isint(comm):
                        msg = "Select " + comm + " recent song(s)"
                    else:
                        if comm.rstrip(" ") != "":
                            msg = "Is '"+comm+"' a number, dick?"
                if flag == "pl":
                    if readFromText("mp pl "+comm) != False:
                        msg = "Play " + str(len(readFromText("mp pl "+comm))) + " songs"
                    else:
                        msg = "Unknown pl (try 'pli')"
                if flag == "pll":
                    if readFromText("mp pl "+comm)  != False:
                        msg = "Load " + str(len(readFromText("mp pl "+comm))) + " songs"
                    else:
                        msg = "Unknown pl (try 'pli')"
            else:
                if musicPaths == []:
                    msg = "Play " + str(len(matchcrit(cur,allfiles))) + " song(s)"
                else:
                    msg = "Play " + str(len(matchcrit(cur,musicPaths))) + " song(s)"
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
        diskdata = []
        diskdata += [os.path.join(settings["searchdir"],name)
            for settings["searchdir"], dirs, files in os.walk(settings["searchdir"])
            for name in files
            if name.endswith((".mp3",".flac",".m4a",".wav"))]
        s.mpfilesget()
        writeToText(diskdata,"mp allfiles")

    def mpfilesget(s): # updates allfiles and mp playcount using osData.txt
        global allfiles
        allfiles = readFromText("mp allfiles")

    def mpinterpret(s,entry): # interprets the given entry command in the context of the music player
        s.entry = " ".join(entry.split())
        s.cflag = entry.split()[0]
        s.UI = entry[len(s.cflag)+1:]
        s.oldpaths = musicPaths
        s.newpaths = musicPaths

        # start by finding what the new desired paths are
        # also run code that doesn't influence paths, eg: playing, refreshing, saving
        if s.cflag == "s":
            s.newpaths = dupl_rem(s.oldpaths+matchcrit(s.UI,allfiles))
            s.log("OSI: Added " + str(len(matchcrit(s.UI,allfiles))) + " song(s)")
        elif s.cflag == "r":
            s.newpaths = dupl_rem(matchcrit(s.UI,s.oldpaths))
            s.log("OSI: Refined to " + str(len(s.newpaths)) + " song(s)")
        elif s.cflag == "d":
            s.newpaths = [x for x in s.oldpaths if x not in matchcrit(s.UI,s.oldpaths)]
            s.log("OSI: Removed " + str(len(s.oldpaths)-len(s.newpaths)) + " song(s)")
        elif s.cflag == "p":
            if s.UI == "" and s.oldpaths != []:
                s.mpplay(s.oldpaths)
            if s.UI != "":
                if s.oldpaths == []:
                    if len(matchcrit(s.UI,allfiles)) != 0:
                        s.mpplay(matchcrit(s.UI,allfiles))
                elif len(matchcrit(s.UI,s.oldpaths)) != 0:
                    s.mpplay(matchcrit(s.UI,s.oldpaths))
        elif s.cflag == "gp":
            print(allfiles[5])
            s.gpsongs = [x for x in allfiles if "/GP\\" in x]
            print("test, gpsongs length is "+str(len(s.gpsongs)))
            s.gpsongs.sort(key=lambda x: os.path.getmtime(x))
            if s.UI == "": temp = -1
            else: temp = -1*int(s.UI)
            s.newpaths = dupl_rem(s.gpsongs[temp:] + s.oldpaths)
        elif s.cflag == "bin":
            if s.UI == "":
                for i in s.oldpaths:
                    send2trash(i)
                s.log("OSI: Sent " + str(len(s.oldpaths)) + " song(s) to trash")
                s.newpaths = []
            else:
                for i in dupl_rem(matchcrit(s.UI,s.oldpaths)):
                    send2trash(i)
                s.newpaths = [x for x in s.oldpaths if x not in matchcrit(s.UI,s.oldpaths)]
                s.log("OSI: Sent " + str(len(s.oldpaths)-len(s.newpaths)) + " song(s) to trash")
            s.mprefresh() # also updates local allfiles
        elif s.cflag == "e":
            s.mpplay([])
        elif s.cflag == "c":
            s.newpaths = []
            s.log("OSI: Cleared selection")
        elif s.cflag == "pl":
            if readFromText(str("mp pl "+s.UI)) != False:
                s.mpplay(readFromText(str("mp pl "+s.UI)))
        elif s.cflag == "plsave":
            if len(s.oldpaths) == 0:
                #logappend("HMP: No song(s) selected")
                pass
            else:
                writeToText(s.oldpaths,str("mp pl "+s.UI))
                s.log("OSI: Saved playlist")
                try:
                    s.mpinterpret("plic")
                    s.mpinterpret("pli")
                except:
                    pass
        elif s.cflag == "pldel":
            if delText("mp pl "+s.UI):
                s.log("OSI: Playlist deleted")
            else:
                s.log("ERR: Playlist deletion failed")
        elif s.cflag == "pll":
            if readFromText(str("mp pl "+s.UI)) != False:
                s.newpaths = dupl_rem(s.oldpaths+readFromText(str("mp pl "+s.UI)))
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
                if len(matchcrit(s.cflag+" "+s.UI,allfiles)) != 0:
                    s.mpplay(matchcrit(s.cflag+" "+s.UI,allfiles))
            else:
                if len(matchcrit(s.cflag+" "+s.UI,s.oldpaths)) != 0:
                    s.mpplay(matchcrit(s.cflag+" "+s.UI,s.oldpaths))

        # now that the new paths are known, update the widgets accordingly
        for i in [x for x in s.newpaths if x not in s.oldpaths]:
            musicWidgets.append(musicLine(i))
        for i in [x for x in s.oldpaths if x not in s.newpaths]:
            musicWidgets[musicPaths.index(i)].remove()
        # place any commands that should run after every entry below this line
        try: s.pliwrapper.tkraise()
        except: pass

    def mpupdate(s): # get all the musicLine widgets to update themselves
        for i in musicWidgets: i.update()

    def mpplay(s,songlist): # function to play a list of .mp3 files with foobar
        #mpcount(songlist)
        s.log("OSI: Playing " + str(len(songlist)) + " song(s)")
        subprocess.Popen([settings["foobarexe"]]+[i for i in songlist])

    def mpplgen(s): # generate the playlist info widget
        # define surrounding layout (regardless of playlists)
        s.pliwrapper = tk.Frame(s.mpframe,bg=tkbuttoncolor)
        s.pliwrapper.pack_propagate(0)
        s.pliframe = tk.Frame(s.pliwrapper,bg=tkbgcolor2)
        s.plikeyframe = tk.Frame(s.pliframe,width=260,height=22,bg=tkbgcolor2)
        s.plikeyframe.pack_propagate(0)
        s.plikeyframe.pack(side=TOP,fill=X,pady=(0,1))
        s.plitextstring = "Name       #S  #A"
        if settings["set_pliduration"]=="True":
            s.plitextstring += "  Length"
        s.plikey = tk.Label(s.plikeyframe,font=fontset,text=s.plitextstring,bg=tkbgcolor2,fg=tktxtcol)
        s.plikey.pack(side=LEFT,anchor=W)
        s.plikeydel = tk.Button(s.plikeyframe,fg=tktxtcol,font=fontset,borderwidth=0,text="X",command=lambda:s.mpinterpret("plic"),bg=tkbuttoncolor)
        s.plikeydel.pack(side=RIGHT)
        # get all playlists + info
        s.plipllist = []  #'playlistinfoplaylistlist' i am excellent at naming things
        for i in searchText("mp pl "):
            s.plipllist.append([i[6:]]) # add name
            s.plipllist[-1].append(str(len(readFromText(i)))) # add number of song(s)
            s.plipllist[-1].append(str(len(dupl_rem([x.split("/")[-1].split("\\")[1] for x in readFromText(i)])))) # add number of artists (mildly proud that this worked in one go)
            if settings["set_pliduration"]=="True":
                s.temp_length = sum([int(MP3(x).info.length) for x in readFromText(i) if '.m4a' not in x])
                s.plipllist[-1].append(str(int(s.temp_length//60))+":"+str(int(s.temp_length%60)))

        for i in s.plipllist:
            pliLine(i)
        s.pliframe.pack(side=TOP,fill=Y,expand=True)
        s.pliwrapper.place(x=630,width=266,height=tkheight)

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
                    target = matchcrit(comm, dbstate[1])
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
                dbloc = dbdir


            else: # open aegis/text/folder
                if flag != "o":
                    comm = flag + " " + comm
                    print("Concatenated comm to "+comm)
                matchresult = matchcrit(comm,dbstate[1])
                if matchresult != []:
                    matchresult = matchresult[0]
                    matchindex = dbstate[1].index(matchresult)
                    if os.path.isdir(rootdir+dbloc+matchresult):
                        dbloc += matchcrit(comm,dbstate[1])[0]+"/"
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
                    dbloc = "/".join(dbloc.split("/")[:-1])+"/"+filterchars(s.dbtitle.get("0.0",END),"\\/*<>:?\"|\n")+".txt"
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
        for i in range(enclevel): data = s.aegenc_single(s.aegkeyparse(keys,True),data)
        for i in range(enclevel): data = s.aegenc_single(s.aegkeyparse(keys,False),data)
        return data

    def aegdec(s,keys,data):
        for i in range(enclevel): data = s.aegdec_single(s.aegkeyparse(keys,False),data)
        for i in range(enclevel): data = s.aegdec_single(s.aegkeyparse(keys,True),data)
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
        if gplogin != True:
            pass
        else:
            s.glbentry.delete("0",len(s.glbentry.get())) # empty the entry field
            if entry.startswith("d ") and isint(entry.split()[1]): # if entry is delete command
                # del
                pass
            elif entry == "dl":
                pass
                # download
            elif entry.startswith("yt"): # yt single song
                pass
            elif entry.startswith(("album", "gpalbum")):
                pass
            elif entry.startswith(("http://","https://","www.","youtube.com","play.google")):
                # if true, start parsing URL
                # remove unnecessary prefixes
                urlentry = entry
                for i in ["http://","https://","www.","youtube.com","play.google",".com","/music/"]:
                    urlentry = urlentry.split(i)[-1]

                # track after parse: m/T2udbfj3fuixwpbos76j7qnixza?t=Let_It_Happen_-_Tame_Impala
                # pl after parse: playlist/AMaBXymHqRhQ9A79nGWS_zkVJLp-tuk7_neTefL7f8a2nWRi5sonzwZ9cuYyHqGwJQbefA_jcWakZgeiD2FncspLGNRjRSkslg%3D%3D
                # album after parse: m/Bfinyskmfffl7mnb5gghboinjbu?t=Currents_-_Tame_Impala

                # for GP: note that album ids start with "B" and tracks start with "T"
                type = "none"
                id = "-"
                if "play.google" in entry:
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
                    s.log("YT not supported yet")
                else:
                    s.log("URL parsing failed")
                s.log(type)
                s.log(id)
                if type == "gp track":
                    api.get_track_info(id)
                if type == "gp playlist":
                    api.get_shared_playlist_contents(id)
                if type == "gp album":
                    api.get_album_info(id)


            elif entry != "" or entry.startswith("gp "):
                # not a command or URL: default behaviour is to search GP for single track
                search_results = s.gpsearch(entry)
                if search_results != False:
                    dlWidgets.append(gpTrack(search_results))

    def gpbackgroundlogin(s):
        from gmusicapi import Mobileclient
        global gplogin
        global api
        api = Mobileclient()
        try:
            gptemp = api.login(settings["gpemail"], gppass, settings["gpMAC"])
        except Exception as e:
            s.dlloginreq.configure(text="LOGIN FAILED")
            print(e)
            return
        gplogin = gptemp
        OSI.log("OSI: GP logged in")
        if gplogin == True:
            s.dlloginreq.pack_forget()
        time.sleep(1)
        OSI.log("OSI: All systems nominal")

    def gpsearch(s,query):
        # perform search of gp database
        try:
            results = api.search(query).get("song_hits",DL_ALTERNATIVES)[:DL_ALTERNATIVES]
        except IndexError:
            gpLineEmpty(query)
            return False
        curinfo = []
        for i in results:
            i = i.get("track")
            # get relevant results in a list
            curinfo.append([
                fltr(str(i.get("title"))),
                fltr(str(i.get("artist"))),
                fltr(str(i.get("album"))),
                str(i.get("albumArtRef")[0].get("url")),
                fltr(str(i.get("trackNumber"))),
                query,
                fltr(str(i.get("composer"))),
                fltr(str(i.get("year"))),
                fltr(str(i.get("beatsPerMinute"))),
                fltr(str(i.get("genre")))
            ])
        return curinfo

    def dl_url2file(s,url,filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # open in binary mode
        with open(filename, "wb") as wfile:
            # get request
            response = requests.get(url)
            # write to file
            wfile.write(response.content)

    def dltagify(s,songpath,tinfo):
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

    def dlalbumartify(s,songpath,folderpath):
        audio = MP3(songpath, ID3=ID3)
        try:audio.add_tags()
        except:pass
        audio.tags.add(APIC(
                encoding=3, # 3 is for utf-8
                mime='image/png', # image/jpeg or image/png
                type=3, # 3 is for the cover image
                desc=u'Cover',
                data=open((folderpath+"/albumArt.png"),'rb').read()))
        audio.save()


    #################################### WORK DEFS #####################################################################

    def wkinterpret(s,entry):
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

    def gitGetEmail(s): # update settings according to git email
        pipe = subprocess.Popen("git config user.email", shell=True, stdout=subprocess.PIPE).stdout
        output = str(pipe.read(), "utf-8").rstrip("\n\r")
        settings["git_email"] = output
        s.updateSettings()

    def gitSetEmail(s): # update git email according to settings
        subprocess.Popen("git config --global user.email "+settings["git_email"])
        s.updateSettings

    def updateSettings(s):
        for i in s.stWidgets: i.update()
        exportSettings()


    #################################### END OF MAINUI #####################################################################

class dlManager:
    def __init__(s):
        s.mainframe = tk.Frame(OSI.dlframe,bg=tkbuttoncolor,height=50)
        s.state = "waiting"

        s.count_gpcomplete = 0
        s.count_gptotal = 0
        s.count_ytcomplete = 0
        s.count_yttotal = 0
        s.gptracks = []
        s.yttracks = []
        s.staticlabel = tk.Label(s.mainframe, bg=tkbuttoncolor,fg=tktxtcol,anchor=W,font=fontset,width=40)
        s.staticlabel.pack(side=LEFT)
        s.gpstatus = tk.Label(s.mainframe, bg=tkbuttoncolor,fg=tktxtcol,anchor=W,font=fontset,width=28)
        s.gpstatus.pack(side=LEFT)
        s.ytstatus = tk.Label(s.mainframe, bg=tkbuttoncolor,fg=tktxtcol,anchor=W,font=fontset,width=28)
        s.ytstatus.pack(side=RIGHT)
        s.refreshvalues()
        s.mainframe.pack(side=BOTTOM)

    def download(s): # publicly accessible download command that is split into further tasks
        if len(gptracks) + len(yttracks) > 0:
            if len(gptracks) > 0:
                s.state = "downloading gp"
            else:
                s.state = "downloading yt"
            s.process_downloads() # start a continuously refreshing loop until all queues are done
        else:
            OSI.log("OSI: Nothing to download")

    def process_downloads(s): # function that updates the downloading process
        # process the top of the gp queue

        # decide if we need to keep downloading
        if len(gptracks) + len(yttracks) > 0:
            root.after(100,s.process_downloads) # continue the loop
        else:
            s.state = "waiting"
        s.refreshvalues()

    def gp_download(s,track): # download a single track
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
        '''

        folderpath = settings["gpdldir"] + track[1] + "/" + track[2] + "/"
        songpath = folderpath + ('00'+track[4])[-2:] + " " + track[0] + ".mp3"
        if os.path.isfile(songpath) and os.path.getSize(songpath) > 0:
            OSI.log("OSI: Skipping (already downloaded)")
        else:
            OSI.gp_url2file(str(api.get_stream_url(track[5])),songpath)
            if "albumArt.png" not in os.listdir(folderpath):
                try:
                    OSI.gp_url2file(track[3],(folderpath+"/albumArt.png"))
                except:
                    print("track[3] failed!")
                    OSI.gp_url2file(result.get("albumArtRef")[0].get("url"),(folderpath+"/albumArt.png"))
            OSI.gpalbumartify(songpath,folderpath)
            OSI.gptagify(songpath,track)

    def refreshvalues(s): # update the tracking labels
        if s.state == "waiting":
            s.staticlabel.configure(text="Status: ready to download")
        if s.state == "downloading gp":
            s.staticlabel.configure(text="Status: downloading from Google Play")
        if s.state == "downloading gp":
            s.staticlabel.configure(text="Status: downloading from YouTube")
        s.gpstatus.configure(text=str(s.count_gpcomplete)+"/"+str(s.count_gptotal))
        s.ytstatus.configure(text=str(s.count_ytcomplete)+"/"+str(s.count_yttotal))

    def queue_gp(s,tracklist): # add tracks to the gp queue
        for i in tracklist:
            s.gptracks.append(i)
            s.count_gptotal += 1

    def queue_yt(s,tracklist): # add tracks to the yt queue
        for i in tracklist:
            s.yttracks.append(i)
            s.count_yttotal += 1

class dlLine: # ABSTRACT
    def __init__(s):
        # root superclass constructor has the elements shared by all possible variations of downloader widget
        # create root window with basic border
        s.wrapper = tk.Frame(OSI.dlframe,height=54)
        s.mainframe = tk.Frame(s.wrapper,bg=tkbuttoncolor)
        s.mainframe.pack(side=TOP,fill=X,padx=2,pady=2)
        s.wrapper.pack(side=TOP,pady=(10,0),padx=10,fill=X)
    def __str__(s):
        return "dbLine (INTERFACE!)"

class gpLine(dlLine):
    def __init__(s):
        dlLine.__init__(s)
    def __str__(s):
        return "gpLine (INTERFACE!)"
    # download method shared by all gp objects
    def download(s,to_dl):
        for x in to_dl:
            folderpath = settings["gpdldir"] + x[1] + "/" + x[2] + "/"
            songpath = folderpath + ('00'+x[4])[-2:] + " " + x[0] + ".mp3"
            if os.path.isfile(songpath):
                pass
            else:
                # OLD CODE:
                # get the same data again, because the result object is needed when requesting url
                #result = api.search(x[5]).get("song_hits",5)[int(s.multi_index)].get("track")
                OSI.gp_url2file(str(api.get_stream_url(result.get("storeId"))),songpath)
                if "albumArt.png" not in os.listdir(folderpath):
                    OSI.gp_url2file(result.get("albumArtRef")[0].get("url"),(folderpath+"/albumArt.png"))
                OSI.dlalbumartify(songpath,folderpath)
                OSI.dltagify(songpath,x)

class gpTrack(gpLine):
    def __init__(s, tracklist):
        gpLine.__init__(s)
        s.tracklist = tracklist
        print(tracklist)
    def __str__(s):
        return "gpTrack"

class gpAlbum(gpLine):
    def __init__(s):
        gpLine.__init__(s)
    def __str__(s):
        return "gpAlbum"

class gpPlaylist(gpLine):
    def __init__(s):
        gpLine.__init__(s)
    def __str__(s):
        return "gpPlaylist"

class ytLine(dlLine):
    def __init__(s):
        dlLine.__init__(s)
    def __str__(s):
        return "ytLine (INTERFACE!)"

class ytSingleLine(ytLine):
    def __init__(s):
        ytLine.__init__(s)
    def __str__(s):
        return "ytSingleLine"

class ytMultiLine(ytLine):
    def __init__(s):
        ytLine.__init__(s)
    def __str__(s):
        return "ytMultiLine"

class stWidget:
    def __init__(s,key,label,col,row,type,altkey=None): # internal settings key, label for user, column in stframe, row in stframe, type of setting (text, bool, file, folder)
        s.key = key
        s.altkey = altkey
        s.type = type
        s.mainframe = tk.Frame(OSI.stframe,bg=tkbuttoncolor,width=300,height=20,bd=0,highlightbackground=tkbgcolor3,highlightcolor=tkbgcolor3,highlightthickness=2)
        s.mainframe.grid(column=col,row=row)
        s.label = tk.Label(s.mainframe, bg=tkbuttoncolor,fg=tktxtcol,text=label, font=fontset,width=60)
        s.label.grid(column=0,row=0)
        if type != "bool":
            s.curlabel = tk.Label(s.mainframe, bg=tkbuttoncolor,fg=tktxtcol,text=settings[key],font=italicfont,width=60)
            s.curlabel.grid(column=0,row=1)
        if type in ["file","folder"]:
            s.changebutton = tk.Button(s.mainframe,text="CHANGE", bg=tkbuttoncolor,activeforeground=tktxtcol,activebackground=tkbgcolor3,width=10,fg=tktxtcol,border=0,font=fontset,command=lambda: OSI.promptSetting(key,type))
            s.changebutton.grid(column=1,row=0,rowspan=2,sticky="NESW")
        elif type == "bool":
            s.switchbutton = tk.Button(s.mainframe,text=settings[key], bg=tkbuttoncolor,width=10,activeforeground=tktxtcol,activebackground=tkbgcolor3,fg=tktxtcol,border=0,font=fontset,command=lambda: OSI.switchSetting(key))
            s.switchbutton.grid(column=1,row=0)
        elif type == "list":
            s.nextbutton = tk.Button(s.mainframe, text="SWITCH", bg=tkbuttoncolor,activeforeground=tktxtcol,activebackground=tkbgcolor3,width=10,fg=tktxtcol,border=0,font=fontset,command=lambda: [OSI.cycleSetting(key,altkey), OSI.gitSetEmail()])
            s.nextbutton.grid(column=1,row=0, rowspan=2,sticky="NESW")

        s.mainframe.grid(column=col,row=row,pady=8,padx=8)

    def update(s):
        if s.type != "bool":
            s.curlabel.configure(text=settings[s.key])
        else:
            s.switchbutton.configure(text=settings[s.key])

class wkLine:
    def __init__(s,text,status,assoc=""):
        s.text = text
        s.status = status
        s.assoc = assoc
        s.id = random()
        if status == 0:
            s.mainframe = tk.Frame(OSI.wktodolist1)
        if status == 1:
            s.mainframe = tk.Frame(OSI.wktodolist2)
        if status == 2:
            s.mainframe = tk.Frame(OSI.wktodolist3)
        s.mainframe.pack_propagate(0)
        s.mainframe.configure(bg=tkbgcolor2,height=25,width=int((tkwidth-2*tkpadding)/3)-4)
        s.leftbutton = tk.Button(s.mainframe,font=smallfont)
        s.leftbutton.pack(side=LEFT)
        s.txtlbl = tk.Label(s.mainframe,bg=tkbgcolor2,text=s.text,font=smallfont)
        s.txtlbl.pack(side=LEFT)
        s.rightbutton = tk.Button(s.mainframe,font=smallfont)
        s.rightbutton.pack(side=RIGHT)
        s.mainframe.pack(side=TOP)
        s.setpos(status)
    def getID(s):
        return s.id
    def setassoc(s):
        OSI.wkassoctext.delete("0.0",END)
        OSI.wkassoctext.insert("0.0",assoc)
    def changepos(s,pos):
        newline = wkLine(s.text,pos,s.assoc)
        wkWidgets.append(newline)
        s.remove()
    def remove(s):
        s.mainframe.destroy()
        del wkWidgets[[x.getID() for x in wkWidgets].index(s.id)]
    def setpos(s,pos):
        if pos == 0:
            s.leftbutton.configure(text="X",command=lambda:s.remove())
            s.rightbutton.configure(text=">",command=lambda:s.changepos(1))
        if pos == 1:
            s.leftbutton.configure(text="<",command=lambda:s.changepos(0))
            s.rightbutton.configure(text=">",command=lambda:s.changepos(2))
        if pos == 2:
            s.leftbutton.configure(text="<",command=lambda:s.changepos(1))
            s.rightbutton.configure(text="X",command=lambda:s.remove())




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


        s.wrapper = tk.Frame(OSI.dbframe,height=25, bg=tkbgcolor3)
        s.wrapper.pack_propagate(0)
        s.mainframe = tk.Frame(s.wrapper,bg=tkbuttoncolor)
        s.indexlabel = tk.Label(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,anchor=W,font=fontset,width=3,text=('00'+str(s.indexval+1))[-2:])
        s.indexlabel.pack(side=LEFT,padx=(10,0))
        s.typelabel = tk.Label(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,anchor=W,font=fontset,width=10)
        s.typelabel.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,anchor=W,font=fontset,width=28)
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
            s.delbutton = tk.Button(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,font=fontset,text="DEL",width=6,relief='ridge',bd=0,activebackground=tkbgcolor, activeforeground=tktxtcol, command=lambda: OSI.dbinterpret("d "+str(s.indexval+1)))
            s.delbutton.pack(side=RIGHT)
        else:
            s.typelabel.configure(text="FOLDER")
        if dbstate[3][s.indexval] not in ["aeg_nokey","aeg_wrongkey"]:
            s.openbutton = tk.Button(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,font=fontset,text="OPEN",width=6,relief='ridge',bd=0,activebackground=tkbgcolor, activeforeground=tktxtcol, command=lambda: OSI.dbinterpret("o "+str(s.indexval+1)))
            s.openbutton.pack(side=RIGHT)
        s.mainframe.pack(side=TOP,fill=X,padx=1,pady=1)
        s.wrapper.pack(side=TOP,pady=(2,0),padx=10,fill=X)

class gpLineEmpty: # !!! move to below music classes when done
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
        s.plisframe = tk.Frame(OSI.pliframe,width=260,height=20, bg=tkbgcolor2)
        s.plisframe.pack_propagate(0)
        s.plitextstring = (s.info[0]+" "*10)[:10]+" "+(s.info[1]+" "*3)[:3]+" "+(s.info[2]+" "*3)[:3]
        if settings["set_pliduration"]=="True":
            s.plitextstring += " "+(s.info[3]+" "*5)[:5]
        s.plitext = tk.Label(s.plisframe,font=fontset,text=s.plitextstring,bg=tkbgcolor2,fg=tktxtcol)
        s.plitext.pack(side=LEFT,anchor=W)
        s.pliplaybtn = tk.Button(s.plisframe,font=fontset,pady=0,borderwidth=0,text="P",bg=tkbgcolor,fg=tktxtcol,command=lambda:OSI.mpinterpret("pl "+s.info[0]))
        s.pliloadbtn = tk.Button(s.plisframe,font=fontset,pady=0,borderwidth=0,text="L",bg=tkbgcolor,fg=tktxtcol,command=lambda:OSI.mpinterpret("pll "+s.info[0]))
        s.plisavebtn = tk.Button(s.plisframe,font=fontset,pady=0,borderwidth=0,text="S",bg=tkbgcolor,fg=tktxtcol,command=lambda:OSI.mpinterpret("plsave "+s.info[0]))
        s.plisavebtn.pack(side=RIGHT,anchor=W)
        s.pliloadbtn.pack(side=RIGHT,anchor=W)
        s.pliplaybtn.pack(side=RIGHT,anchor=W)
        s.plisframe.pack(side=TOP,fill=X,pady=1)

class musicLine:
    def __init__(s,path):

        s.path = "\\".join(path.split("\\"))
        musicPaths.append(s.path)
        s.index = musicPaths.index(s.path)

        # defining single song widget layout
        s.mainframe = tk.Frame(OSI.mpframe,highlightthickness=0,width=tkwidth-20,height=28,bd=0)
        s.mainframe.pack_propagate(0)
        s.indexlabel = tk.Label(s.mainframe,font=fontset,fg=tktxtcol,width=3,anchor=W,text=(("00"+str(int(s.index)+1))[-2:]))
        s.indexlabel.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe,font=fontset,fg=tktxtcol,width=45,anchor=W)
        if isint(s.path.split("/")[-1].split("\\")[3].split()[0]):
            s.titlelabel.configure(text=" ".join(s.path.split("/")[-1].split("\\")[3].split()[1:])[:-4])
        else:
            s.titlelabel.configure(text=" ".join(s.path.split("/")[-1].split("\\")[3].split())[:-4])

        s.titlelabel.pack(side=LEFT,padx=(0,15))
        s.artistlabel = tk.Label(s.mainframe,font=fontset,fg=tktxtcol,width=30,anchor=W,text=s.path.split("/")[-1].split("\\")[1])
        s.artistlabel.pack(side=LEFT,padx=(0,15))
        s.albumlabel = tk.Label(s.mainframe,font=fontset,fg=tktxtcol,width=25,anchor=W,text=s.path.split("/")[-1].split("\\")[2])
        s.albumlabel.pack(side=LEFT)
        s.buttonframe = tk.Frame(s.mainframe,highlightthickness=0,bd=0,width=60,height=s.mainframe.cget("height"))
        s.buttonframe.pack_propagate(0)
        s.destroybutton = tk.Button(s.buttonframe,font=fontset,bg=tkbgcolor3,fg=tktxtcol,command=s.remove,text="X",width=2,relief="flat")
        s.destroybutton.pack(side=RIGHT,pady=(0,0))
        s.playbutton = tk.Button(s.buttonframe,font=fontset,bg=tkbgcolor3,fg=tktxtcol,command=lambda:OSI.mpplay([s.path]),text="P",width=2,relief="flat")
        s.playbutton.pack(side=RIGHT,padx=(0,0),pady=(0,0))
        s.buttonframe.pack(side=RIGHT,pady=(0,0))
        s.mainframe.pack(side=TOP,fill=X)
        s.widgetlist = [s.mainframe,s.indexlabel,s.titlelabel,s.artistlabel,s.albumlabel,s.buttonframe]
        s.altlist = [s.destroybutton,s.playbutton]
        if int(s.index%2==0):
            for i in s.widgetlist:i.configure(bg=tkbgcolor2)
            #for i in s.altlist:i.configure(bg=tkbgcolor)
        else:
            for i in s.widgetlist:i.configure(bg=tkbgcolor)
            #for i in s.altlist:i.configure(bg=tkbgcolor2)

    def update(s):
        s.index = musicPaths.index(s.path)
        s.indexlabel.configure(text=(("00"+str(int(s.index)+1))[-2:]))
        if int(s.index%2==0):
            for i in s.widgetlist:i.configure(background=tkbgcolor2)
        else:
            for i in s.widgetlist:i.configure(background=tkbgcolor)

    def remove(s):
        s.update()
        del musicPaths[s.index]
        s.mainframe.destroy()
        del musicWidgets[s.index]
        OSI.mpupdate()


# LAUNCH PREP
root = tk.Tk()
OSI = mainUI(root)
dlMan = dlManager()
OSI.greet()

for i in range(3):
    wkWidgets.append(wkLine("herro "+str(i),1))

# root operations first
getattention(root)
if settings["set_notitle"]=="True":
    OSI.buttonframe.bind('<B1-Motion>', move_window)
    OSI.buttonframe.bind('<Button-1>', def_delta)
    root.overrideredirect(True)
    geomheight = str(tkheight)#+70)
    geomwidth = str(tkwidth)#+312)
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

OSI.mpfilesget()

# db
OSI.glbentry.bind("<Key>", lambda x: root.after(10,OSI.responsive))
OSI.dbtitle.bind("<Tab>", OSI.dbfocusedit)
OSI.glbentry.bind("<Tab>", OSI.dbfocusedit)
OSI.dbeditor.bind("<Tab>", OSI.dbfocusentry)

OSI.dbrefresh()

OSI.log("OSI: MP and DB loaded")

api = None # this is imported asynchronously due to long delay (.6 seconds)
gplogin = False
gppass = settings["gppass"]
threading.Thread(target=OSI.gpbackgroundlogin).start()

# settings
OSI.stWidgets = [stWidget("searchdir","Music folder",0,0,"folder"),
                stWidget("gpdldir","Download folder",0,1,"folder"),
                stWidget("foobarexe","Foobar EXE",0,2,"file"),
                stWidget("set_notitle","Use own title bar instead of windows",0,3,"bool"),
                stWidget("set_pliduration","Show lengths of playlists in 'pli' menu",0,4,"bool"),
                stWidget("set_update","Get updates from foobar",0,5,"bool"),
                stWidget("set_foobarplaying","Show currently playing song",0,6,"bool"),
                stWidget("git_email","Git Email",1,0,"list","git_emails")]

OSI.gitGetEmail()
root.mainloop()
