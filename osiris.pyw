# Continuation of the first tkinter shell, nicknamed Osiris
# note that 's.' was used instead of 'self.' because I am an ungodly bastard
# and / or because I am lazy
#
# - RFK 2018 -

# built-in libraries
# import time
# timing module: uncomment and call t_since_start() anywhere
# starting_time = time.time()
# def t_since_start(): print(time.time() - starting_time)
import os
import logging  # used to quiet gmusicapi warnings

# window fuckery libaries
from ctypes import windll

# third party libraries

# establishing location and settings
rootdir = os.path.dirname(os.path.realpath(__file__)) + "/"
os.chdir(rootdir)

# own classes
from src.main_ui import *
from src.dl_manager import *
from src.widgets.st_widgets import *


# setup
mousex, mousey = 0, 0  # initialise mouse locations

# create the database root directory
if not os.path.exists(DB_DIR):
    os.mkdir(DB_DIR)

# make gmusicapi shut up
logging.disable(logging.CRITICAL)

# disgusting windows fuckery to make top bar disappear
GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080


def set_appwindow(window_root):  # let the window have a taskbar icon
    hwnd = windll.user32.GetParent(window_root.winfo_id())
    style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style = style & ~WS_EX_TOOLWINDOW
    style = style | WS_EX_APPWINDOW
    windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    window_root.wm_withdraw()
    root.after(10, lambda: root.wm_deiconify())


# TOPLEVEL UTILITY FUNCTIONS
# lift the root above other windows and focus on the entry field
def get_attention():
    root.lift()
    root.attributes("-topmost", True)
    root.attributes("-topmost", False)
    root.after(10, lambda: set_appwindow(root))
    root.after(200, lambda: root.focus_force())
    root.after(300, lambda: OSI.glbentry.focus())


# adjust recorded mouse location according to event
def def_delta(event):
    global mousex, mousey
    mousex = event.x
    mousey = event.y


# move the window with the mouse
def move_window(event):
    if settings["set_draggable"] == "True":
        root.geometry("+" + str(event.x_root - mousex) + "+" + str(event.y_root - mousey))


# TOP LEVEL WIBBLY WOBBLY UPDATER
def update():  # function that gets called every second to update assorted
    try:
        # note that this function needs to be as lightweight as possible
        # use if statements that avoid unnecessary work outside Osiris
        global foobarprev
        global photo
        # foobar currently playing widget
        foobarnow = [open("etc/foobar_nowplaying.txt", "r").readlines()][0][0].rstrip("\n")[3:]
        if foobarnow.startswith("not running"):
            OSI.mpfoobarplaypause.configure(text="Foobar not running")
        elif foobarnow.startswith("paused:"):
            if settings["hide_foobarplaying_on_pause"] == "True" and OSI.mpfoobarwrapper.winfo_ismapped():
                OSI.mpfoobarwrapper.place_forget()
            else:
                OSI.mpfoobarplaypause.configure(text="Paused")
        else:
            if settings["hide_foobarplaying_on_pause"] == "True" and not OSI.mpfoobarwrapper.winfo_ismapped():
                OSI.mpfoobarwrapper.place(x=1090, y=840, height=100, width=500)
            else:
                OSI.mpfoobarplaypause.configure(text="Playing")

        if foobarnow != foobarprev:
            image = Image.open(("/".join(foobarnow.lstrip("playing: ").split("\\")[:-1])) + "/albumArt.png")
            image = image.resize((100, 100), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(image)
            OSI.mpfoobaralbart.configure(image=photo)

            maincolor = color_from_image(image)

            if (max(maincolor) + min(maincolor)) / 2 >= 127:
                contrast = "#000000"
            else:
                contrast = COLOR_TEXT

            bordercolor = rgb_to_hex(maincolor)
            OSI.mpfoobarwrapper.configure(bg=bordercolor)

            temp = foobarnow[len("playing: "):].split("\\")
            OSI.mpfoobarframe.configure(bg=bordercolor)
            OSI.mpfoobar_song.configure(text=temp[-1][3:-4], bg=bordercolor, fg=contrast)
            OSI.mpfoobar_artist.configure(text=temp[-3], bg=bordercolor, fg=contrast)
            OSI.mpfoobar_album.configure(text=temp[-2], bg=bordercolor, fg=contrast)
            OSI.mpfoobarplaypause.configure(bg=bordercolor, fg=contrast)
            foobarprev = foobarnow[:]
        root.after(1000, update)
    except OSError:
        root.after(1000, update)


# LAUNCH PREP
root = tk.Tk()
OSI = MainUI(root, rootdir)
DLMAN = DownloadManager(OSI)
OSI.DLMAN = DLMAN
OSI.greet()

# root operations first

if settings["set_notitle"] == "True":
    OSI.buttonframe.bind('<B1-Motion>', move_window)
    OSI.buttonframe.bind('<Button-1>', def_delta)
    root.overrideredirect(True)
    geomheight = str(TK_HEIGHT)  # +70)
    geomwidth = str(TK_WIDTH)  # +312)
    root.geometry(geomwidth + "x" + geomheight + "+0+0")

if settings["set_update"] == "True":
    foobarprev = ""
    root.after(0, update)

root.iconbitmap("etc/osi.ico")

if settings["set_showscrollbar"] == "True":
    root.after(50, lambda: OSI.scrollcanvas.config(scrollregion=OSI.scrollcanvas.bbox("all")))

OSI.rootframe.bind("<FocusIn>", lambda x: OSI.attempt_maximise())
root.bind("<Alt-v>", lambda x: OSI.attempt_minimise())

# OSI operations
bindlist = [root, OSI.glbentry, OSI.dbeditor, OSI.dbtitle]
for i in bindlist:
    i.bind("[", OSI.tab_left)
    i.bind("]", OSI.tab_right)

# mp

OSI.mp_page_handler = PageHandler(OSI, "mp", MP_PAGE_SIZE)

OSI.mp_refresh()

# db
OSI.glbentry.bind("<Key>", lambda x: root.after(10, OSI.responsive))
OSI.dbtitle.bind("<Tab>", OSI.db_switch_focus)
OSI.glbentry.bind("<Tab>", OSI.db_switch_focus)
OSI.dbeditor.bind("<Tab>", OSI.db_focus_entry)

OSI.db_refresh()

OSI.log("OSI: MP and DB loaded")

api = None  # this is imported asynchronously due to long delay (.6 seconds)
webapi = None
gplogin = False
threading.Thread(target=OSI.db_login_gp).start()

# settings
OSI.st_widgets = [StWidget(OSI, "searchdir", "Music folder", 0, 0, "folder"),
                  StWidget(OSI, "dldir", "Download folder", 0, 1, "folder"),
                  StWidget(OSI, "foobarexe", "Foobar EXE", 0, 2, "file"),
                  StWidget(OSI, "set_notitle", "Use own title bar instead of windows", 0, 3, "bool"),
                  StWidget(OSI, "set_pliduration", "Show lengths of playlists in 'pli' menu", 0, 4, "bool"),
                  StWidget(OSI, "set_update", "Get updates from foobar", 0, 5, "bool"),
                  StWidget(OSI, "set_draggable", "Make window draggable with mouse", 0, 6, "bool"),
                  StWidget(OSI, "set_foobarplaying", "Show currently playing song", 1, 0, "bool"),
                  StWidget(OSI, "hide_foobarplaying_on_pause", "Hide current song if paused", 1, 1, "bool")]

get_attention()
root.mainloop()
