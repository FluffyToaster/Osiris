from src.settings import *

import tkinter as tk
from tkinter import LEFT, RIGHT, TOP, CENTER, X, Y
from io import BytesIO

# third party libraries
import requests
from PIL import Image, ImageTk  # use Pillow for python 3.x


class DlWidget:  # ABSTRACT
    def __init__(s):
        # root superclass constructor has the elements shared by all possible variations of downloader widget
        # create root window with basic border
        s.wrapper = tk.Frame(OSI.dlframe, height=54)
        s.mainframe = tk.Frame(s.wrapper,
                               bg=COLOR_BUTTON)  # placeholder mainframe that is replaced by the generate function
        s.mainframe.pack(side=TOP, fill=X, padx=2, pady=2)

    def __str__(s):
        return "DbLine (INTERFACE!)"

    def generate(s):
        # every generate function should at least destroy the mainframe and replace it with its own
        s.mainframe.destroy()
        s.mainframe = tk.Frame(s.wrapper, bg=COLOR_BUTTON)
        s.mainframe.pack(side=TOP, fill=X, padx=2, pady=2)
        try:
            s.multiframe.destroy()
        except:
            pass  # no multiframe to destroy

    def show(s):
        s.wrapper.pack(side=TOP, pady=(10, 0), padx=10, fill=X)

    def hide(s):
        if s.wrapper.winfo_ismapped():
            s.wrapper.pack_forget()

    def set_color(s, color):
        if type(color) != str and len(color) == 3:
            color = rgb_to_hex(color)
        s.wrapper.configure(bg=color)

    def multipack(s):
        s.multibutton.configure(command=s.multiforget)
        s.multiframe.pack(side=TOP, fill=X)

    def multiforget(s):
        s.multibutton.configure(command=s.multipack)
        s.multiframe.pack_forget()


class GpLine(DlWidget):
    def __init__(s):
        DlWidget.__init__(s)

    def __str__(s):
        return "GpLine (INTERFACE!)"


# noinspection PyMethodParameters,PyMethodParameters
class GpTrack(GpLine):
    def __init__(s, tracklist):
        GpLine.__init__(s)
        s.tracklist = tracklist
        s.multi_index = 0  # which song to select in the tracklist
        s.generate()

    def __str__(s):
        return "GpTrack"

    def generate(s):  # use tracklist and multi_index to generate the widget as desired
        DlWidget.generate(s)  # regenerate mainframe

        curinfo = s.tracklist[s.multi_index]
        s.image = Image.open(BytesIO(requests.get(curinfo[3]).content))
        s.image = s.image.resize((50, 50), Image.ANTIALIAS)
        # get the main color from the image for fancy reasons
        s.bordercolor = color_from_image(s.image)

        if (max(s.bordercolor) + min(s.bordercolor)) / 2 >= 127:
            s.bordercontrast = "#000000"
        else:
            s.bordercontrast = COLOR_TEXT
        s.bordercolor = rgb_to_hex(s.bordercolor)
        s.typelabel = tk.Label(s.mainframe, bg=s.bordercolor, fg=s.bordercontrast, anchor=CENTER,
                               font=(FONT_M[0], FONT_M[1], 'bold'), width=8, text="Track")
        s.typelabel.pack(side=LEFT, fill=Y)

        s.set_color(s.bordercolor)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe, height=50, width=50, bg=COLOR_BUTTON)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe, anchor="w", image=s.photo, borderwidth=0, highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28,
                                text=curinfo[0])
        s.titlelabel.pack(side=LEFT, padx=(10, 0))
        s.artistlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28,
                                 text=curinfo[1])
        s.artistlabel.pack(side=LEFT, padx=(10, 0))
        s.albumlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28,
                                text=curinfo[2])
        s.albumlabel.pack(side=LEFT, padx=(10, 0))
        s.delbutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="X", width=3,
                                relief='ridge', bd=2, activebackground="#c41313", activeforeground=COLOR_TEXT,
                                highlightbackground=s.bordercolor, highlightcolor=s.bordercolor,
                                command=lambda: OSI.dl_delete(s))
        s.delbutton.pack(side=RIGHT, padx=(0, 8))
        s.readybutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="OK", width=3,
                                  relief='ridge', bd=2, activebackground="green", activeforeground=COLOR_TEXT,
                                  highlightbackground=s.bordercolor, highlightcolor=s.bordercolor, command=s.ready)
        s.readybutton.pack(side=RIGHT, padx=(0, 8))

        if len(s.tracklist) > 1:  # if we actually have alternatives to show, make the multilist
            s.multibutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="ALT", width=5,
                                      relief='ridge', bd=2, highlightbackground=s.bordercolor,
                                      highlightcolor=s.bordercolor, activebackground=COLOR_BUTTON,
                                      activeforeground=COLOR_TEXT, command=s.multipack)
            s.multibutton.pack(side=RIGHT, padx=(0, 8))
            s.multiframe = tk.Frame(s.wrapper,
                                    bg=s.wrapper.cget("bg"))  # indeed not packed, that is done by the multibutton
            for i in range(len(s.tracklist)):
                if i != s.multi_index:  # only generate multilines for nonselected tracks
                    s.GpTrackMulti(s, s.tracklist[i], i)

    def ready(s):  # send relevant data to DownloadManager
        DLMAN.queue_gp([s.tracklist[s.multi_index]])
        s.wrapper.destroy()

    # noinspection PyMethodParameters,PyMethodParameters
    class GpTrackMulti:  # GpTrack subclass that just displays a small line
        def __init__(s, parent, info, my_index):
            s.parent = parent
            s.info = info
            s.my_index = my_index
            s.mainframe = tk.Frame(s.parent.multiframe, bg=COLOR_BUTTON)
            s.titlelabel = tk.Label(s.mainframe, anchor="w", font=FONT_M, bg=COLOR_BUTTON, fg=COLOR_TEXT, width=28,
                                    text=info[0])
            s.titlelabel.pack(side=LEFT, padx=(106, 0))
            s.artistlabel = tk.Label(s.mainframe, anchor="w", font=FONT_M, bg=COLOR_BUTTON, fg=COLOR_TEXT, width=28,
                                     text=info[1])
            s.artistlabel.pack(side=LEFT, padx=(10, 0))
            s.albumlabel = tk.Label(s.mainframe, anchor="w", font=FONT_M, bg=COLOR_BUTTON, fg=COLOR_TEXT, width=35,
                                    text=info[2])
            s.albumlabel.pack(side=LEFT, padx=(10, 0))
            s.btn = tk.Button(s.mainframe, text="S", width=2, relief='ridge', bd=2, bg=COLOR_BUTTON, fg=COLOR_TEXT,
                              activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT, command=s.select)
            s.btn.pack(side=RIGHT, padx=(0, 10), pady=2)
            s.mainframe.pack(side=TOP, fill=X, padx=1, pady=(0, 1))

        def select(s):
            s.parent.multi_index = s.my_index
            s.parent.generate()


# noinspection PyMethodParameters,PyMethodParameters,PyMethodParameters
class GpAlbum(GpLine):
    def __init__(s, albumlist):
        GpLine.__init__(s)
        s.albumlist = albumlist
        s.multi_index = 0

        s.generate()

    def __str__(s):
        return "GpAlbum"

    def ready(s):  # send relevant data to DownloadManager
        album_tracks = api.get_album_info(s.albumlist[s.multi_index][4])["tracks"]
        DLMAN.queue_gp([OSI.gp_get_track_data(x) for x in album_tracks])
        s.wrapper.destroy()

    def generate(s):
        DlWidget.generate(s)  # regenerate mainframe

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
        s.image = s.image.resize((50, 50), Image.ANTIALIAS)
        # get the main color from the image for fancy reasons
        s.bordercolor = color_from_image(s.image)

        if (max(s.bordercolor) + min(s.bordercolor)) / 2 >= 127:
            s.bordercontrast = "#000000"
        else:
            s.bordercontrast = COLOR_TEXT
        s.bordercolor = rgb_to_hex(s.bordercolor)
        s.typelabel = tk.Label(s.mainframe, bg=s.bordercolor, fg=s.bordercontrast, anchor=CENTER,
                               font=(FONT_M[0], FONT_M[1], 'bold'), width=8, text="Album")
        s.typelabel.pack(side=LEFT, fill=Y)

        s.set_color(s.bordercolor)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe, height=50, width=50, bg=COLOR_BUTTON)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe, anchor="w", image=s.photo, borderwidth=0, highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28,
                                text=curinfo[0])
        s.titlelabel.pack(side=LEFT, padx=(10, 0))
        s.artistlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28,
                                 text=curinfo[1])
        s.artistlabel.pack(side=LEFT, padx=(10, 0))
        s.delbutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="X", width=3,
                                relief='ridge', bd=2, activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT,
                                highlightbackground=s.bordercolor, highlightcolor=s.bordercolor,
                                command=lambda: OSI.dl_delete(s))
        s.delbutton.pack(side=RIGHT, padx=(0, 8))
        s.readybutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="OK", width=3,
                                  relief='ridge', bd=2, activebackground="green", activeforeground=COLOR_TEXT,
                                  highlightbackground=s.bordercolor, highlightcolor=s.bordercolor, command=s.ready)
        s.readybutton.pack(side=RIGHT, padx=(0, 8))

        if len(s.albumlist) > 1:  # if we actually have alternatives to show, make the multilist
            s.multibutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="ALT", width=5,
                                      relief='ridge', bd=2, highlightbackground=s.bordercolor,
                                      highlightcolor=s.bordercolor, activebackground=COLOR_BUTTON,
                                      activeforeground=COLOR_TEXT, command=s.multipack)
            s.multibutton.pack(side=RIGHT, padx=(0, 8))
            s.multiframe = tk.Frame(s.wrapper,
                                    bg=s.wrapper.cget("bg"))  # indeed not packed, that is done by the multibutton
            for i in range(len(s.albumlist)):
                if i != s.multi_index:  # only generate multilines for nonselected tracks
                    s.GpAlbumMulti(s, s.albumlist[i], i)

    # noinspection PyMethodParameters,PyMethodParameters
    class GpAlbumMulti:  # GpAlbum subclass that just displays a small line
        def __init__(s, parent, info, my_index):
            s.parent = parent
            s.info = info
            s.my_index = my_index
            s.mainframe = tk.Frame(s.parent.multiframe, bg=COLOR_BUTTON)
            s.titlelabel = tk.Label(s.mainframe, anchor="w", font=FONT_M, bg=COLOR_BUTTON, fg=COLOR_TEXT, width=28,
                                    text=info[0])
            s.titlelabel.pack(side=LEFT, padx=(106, 0))
            s.artistlabel = tk.Label(s.mainframe, anchor="w", font=FONT_M, bg=COLOR_BUTTON, fg=COLOR_TEXT, width=28,
                                     text=info[1])
            s.artistlabel.pack(side=LEFT, padx=(10, 0))
            s.btn = tk.Button(s.mainframe, text="S", width=3, relief='ridge', bd=2, bg=COLOR_BUTTON, fg=COLOR_TEXT,
                              activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT, command=s.select)
            s.btn.pack(side=RIGHT, padx=(0, 10), pady=2)
            s.mainframe.pack(side=TOP, fill=X, padx=1, pady=(0, 1))

        def select(s):
            s.parent.multi_index = s.my_index
            s.parent.generate()


# noinspection PyMethodParameters,PyMethodParameters
class GpPlaylist(GpLine):
    def __init__(s, tracklist, plinfo):
        GpLine.__init__(s)
        s.plinfo = plinfo
        s.tracklist = tracklist
        s.generate()

    def __str__(s):
        return "GpPlaylist"

    def ready(s):  # send relevant data to DownloadManager
        DLMAN.queue_gp(s.tracklist)
        s.wrapper.destroy()

    def generate(s):
        DlWidget.generate(s)  # regenerate mainframe

        curinfo = s.plinfo
        s.bordercolor = "#fe5722"
        s.bordercontrast = "#ffffff"
        s.typelabel = tk.Label(s.mainframe, bg=s.bordercolor, fg=s.bordercontrast, anchor=CENTER,
                               font=(FONT_M[0], FONT_M[1], 'bold'), width=8, text="Playlist")
        s.typelabel.pack(side=LEFT, fill=Y)

        s.image = Image.open("etc/gp.png")
        s.image = s.image.resize((50, 50), Image.ANTIALIAS)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe, height=50, width=50, bg=COLOR_BUTTON)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe, anchor="w", image=s.photo, borderwidth=0, highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)

        s.set_color(s.bordercolor)
        s.titlelabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28,
                                text=curinfo[0])
        s.titlelabel.pack(side=LEFT, padx=(10, 0))
        s.artistlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28,
                                 text=curinfo[1])
        s.artistlabel.pack(side=LEFT, padx=(10, 0))
        s.albumlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=12,
                                text=curinfo[2] + " tracks")
        s.albumlabel.pack(side=LEFT, padx=(10, 0))
        s.delbutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="X", width=3,
                                relief='ridge', bd=2, activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT,
                                highlightbackground=s.bordercolor, highlightcolor=s.bordercolor,
                                command=lambda: OSI.dl_delete(s))
        s.delbutton.pack(side=RIGHT, padx=(0, 8))
        s.readybutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="OK", width=3,
                                  relief='ridge', bd=2, activebackground="green", activeforeground=COLOR_TEXT,
                                  highlightbackground=s.bordercolor, highlightcolor=s.bordercolor, command=s.ready)
        s.readybutton.pack(side=RIGHT, padx=(0, 8))


# noinspection PyMethodParameters
class YtLine(DlWidget):
    def __init__(s):
        DlWidget.__init__(s)

    def __str__(s):
        return "YtLine (INTERFACE!)"


# noinspection PyMethodParameters,PyMethodParameters
class YtSingle(YtLine):
    def __init__(s, tracklist):
        YtLine.__init__(s)
        s.tracklist = tracklist
        s.multi_index = 0  # which song to select in the tracklist
        s.generate()

    def __str__(s):
        return "YtSingle"

    def ready(s):  # send relevant data to DownloadManager
        DLMAN.queue_yt([s.tracklist[s.multi_index]])
        s.wrapper.destroy()

    def generate(s):
        DlWidget.generate(s)  # regenerate mainframe

        DLMAN.generate_image_data(s.tracklist, s.multi_index)  # appends image object and primary color to info
        curinfo = s.tracklist[s.multi_index]

        s.bordercolor = curinfo[5]
        s.image = curinfo[4].resize((50, 50), Image.ANTIALIAS)
        # get the main color from the image for fancy reasons

        if (max(s.bordercolor) + min(s.bordercolor)) / 2 >= 127:
            s.bordercontrast = "#000000"
        else:
            s.bordercontrast = COLOR_TEXT
        s.bordercolor = rgb_to_hex(s.bordercolor)
        s.typelabel = tk.Label(s.mainframe, bg=s.bordercolor, fg=s.bordercontrast, anchor=CENTER,
                               font=(FONT_M[0], FONT_M[1], 'bold'), width=8, text="YouTube")
        s.typelabel.pack(side=LEFT, fill=Y)

        s.set_color(s.bordercolor)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe, height=50, width=50, bg=COLOR_BUTTON)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe, anchor="w", image=s.photo, borderwidth=0, highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=90,
                                text=curinfo[0])
        s.titlelabel.pack(side=LEFT, padx=(10, 0))
        s.artistlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=30,
                                 text=curinfo[1])
        s.artistlabel.pack(side=LEFT, padx=(10, 0))
        s.delbutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="X", width=3,
                                relief='ridge', bd=2, activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT,
                                highlightbackground=s.bordercolor, highlightcolor=s.bordercolor,
                                command=lambda: OSI.dl_delete(s))
        s.delbutton.pack(side=RIGHT, padx=(0, 8))
        s.readybutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="OK", width=3,
                                  relief='ridge', bd=2, activebackground="green", activeforeground=COLOR_TEXT,
                                  highlightbackground=s.bordercolor, highlightcolor=s.bordercolor, command=s.ready)
        s.readybutton.pack(side=RIGHT, padx=(0, 8))

        if len(s.tracklist) > 1:  # if we actually have alternatives to show, make the multilist
            s.multibutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="ALT", width=5,
                                      relief='ridge', bd=2, highlightbackground=s.bordercolor,
                                      highlightcolor=s.bordercolor, activebackground=COLOR_BUTTON,
                                      activeforeground=COLOR_TEXT, command=s.multipack)
            s.multibutton.pack(side=RIGHT, padx=(0, 8))
            s.multiframe = tk.Frame(s.wrapper,
                                    bg=s.wrapper.cget("bg"))  # indeed not packed, that is done by the multibutton
            for i in range(len(s.tracklist)):
                if i != s.multi_index:  # only generate multilines for nonselected tracks
                    s.YtSingleMulti(s, s.tracklist[i], i)

    # noinspection PyMethodParameters
    class YtSingleMulti:
        def __init__(s, parent, info, my_index):
            s.parent = parent
            s.info = info
            s.my_index = my_index
            s.mainframe = tk.Frame(s.parent.multiframe, bg=COLOR_BUTTON)
            s.titlelabel = tk.Label(s.mainframe, anchor="w", font=FONT_M, bg=COLOR_BUTTON, fg=COLOR_TEXT, width=90,
                                    text=info[0])
            s.titlelabel.pack(side=LEFT, padx=(106, 0))
            s.artistlabel = tk.Label(s.mainframe, anchor="w", font=FONT_M, bg=COLOR_BUTTON, fg=COLOR_TEXT, width=30,
                                     text=info[1])
            s.artistlabel.pack(side=LEFT, padx=(10, 0))
            s.btn = tk.Button(s.mainframe, text="S", width=2, relief='ridge', bd=2, bg=COLOR_BUTTON, fg=COLOR_TEXT,
                              activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT, command=s.select)
            s.btn.pack(side=RIGHT, padx=(0, 10), pady=2)
            s.mainframe.pack(side=TOP, fill=X, padx=1, pady=(0, 1))

        def select(s):
            s.parent.multi_index = s.my_index
            s.parent.generate()


# noinspection PyMethodParameters
class YtMulti(YtLine):
    def __init__(s, tracklist, plinfo):
        YtLine.__init__(s)
        s.tracklist = tracklist
        s.plinfo = plinfo
        s.multi_index = 0  # which song to select in the tracklist
        s.generate()

    def __str__(s):
        return "YtMulti"

    def ready(s):
        DLMAN.queue_yt(s.tracklist)
        s.wrapper.destroy()

    def generate(s):
        DlWidget.generate(s)  # regenerate mainframe

        curinfo = s.plinfo
        s.bordercolor = "#fe0000"
        s.bordercontrast = "#ffffff"
        s.typelabel = tk.Label(s.mainframe, bg=s.bordercolor, fg=s.bordercontrast, anchor=CENTER,
                               font=(FONT_M[0], FONT_M[1], 'bold'), width=8, text="Playlist")
        s.typelabel.pack(side=LEFT, fill=Y)

        s.image = Image.open("etc/yt.png")
        s.image = s.image.resize((50, 50), Image.ANTIALIAS)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe, height=50, width=50, bg=COLOR_BUTTON)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe, anchor="w", image=s.photo, borderwidth=0, highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)

        s.set_color(s.bordercolor)
        s.titlelabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28,
                                text=curinfo[0])
        s.titlelabel.pack(side=LEFT, padx=(10, 0))
        s.artistlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28,
                                 text=curinfo[1])
        s.artistlabel.pack(side=LEFT, padx=(10, 0))
        s.albumlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=12,
                                text=str(curinfo[2]) + " tracks")
        s.albumlabel.pack(side=LEFT, padx=(10, 0))
        s.delbutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="X", width=3,
                                relief='ridge', bd=2, activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT,
                                highlightbackground=s.bordercolor, highlightcolor=s.bordercolor,
                                command=lambda: OSI.dl_delete(s))
        s.delbutton.pack(side=RIGHT, padx=(0, 8))
        s.readybutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="OK", width=3,
                                  relief='ridge', bd=2, activebackground="green", activeforeground=COLOR_TEXT,
                                  highlightbackground=s.bordercolor, highlightcolor=s.bordercolor, command=s.ready)
        s.readybutton.pack(side=RIGHT, padx=(0, 8))

class GpLineEmpty:  # !!! move to below music classes when done
    def __init__(s, query):
        s.mainframe = tk.Frame(OSI.dlframe, highlightthickness=2, highlightbackground="white")
        s.emptylabel = tk.Label(s.mainframe, fg="#c41313", text=("NO MATCH: " + query))
        s.emptylabel.pack(side=TOP)
        s.mainframe.pack(side=TOP, pady=(10, 0), padx=10, fill=X)
        root.after(3000, s.remove)

    def remove(s):
        s.mainframe.pack_forget()
        s.mainframe.destroy()