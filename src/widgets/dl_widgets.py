from src.settings import *
from src.utilities import *

import tkinter as tk
from tkinter import LEFT, RIGHT, TOP, CENTER, X, Y
from mutagen.mp3 import EasyMP3, MP3
from mutagen.id3 import ID3, APIC
from io import BytesIO
import os

# third party libraries
import requests
from PIL import Image, ImageTk  # use Pillow for python 3.x


# UTILITY FUNCTIONS
# find the borders of an image
def findborders(image):
    row = 0
    col = 0
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
    return borderleft, bordertop, borderright, borderbottom


# get the track data of a YT track
def yt_get_track_data(track):
    try:
        vid_id = track["contentDetails"]["videoId"]
    except (KeyError, TypeError):
        try:
            vid_id = track["id"]["videoId"]
        except (KeyError, TypeError):
            vid_id = track["id"]

    return [filter_(str(track["snippet"]["title"])),
            filter_(str(track["snippet"]["channelTitle"])),
            str(track["snippet"]["thumbnails"]["high"]["url"]),
            str(vid_id)]


def gp_get_track_data(track):
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


def gp_get_album_data(album):
    return [filter_(str(album.get("name"))),
            filter_(str(album.get("artist"))),
            filter_(str(album.get("year"))),
            str(album.get("albumArtRef")),
            filter_(str(album.get("albumId"))),
            filter_(str(album.get("explicitType")))]


def dl_url2file(url, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    # open in binary mode
    with open(filename, "wb") as wfile:
        # get request
        response = requests.get(url)
        # write to file
        wfile.write(response.content)


def dl_tagify_mp3(songpath, tinfo):
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


def dl_albumart_mp3(songpath, imagepath):
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
        data=open(imagepath, 'rb').read()))
    audio.save()


def get_correct_channel_name(track):
    trackres = requests.get(
        "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + track[3] + "&key=" + settings[
            "yt_api_key"])
    actual_channel = trackres.json()["items"][0]["snippet"]["channelTitle"]
    return actual_channel


def generate_image_data(tracklist, _index=None):
    if _index is not None:
        curinfo = tracklist[_index]
    else:
        curinfo = tracklist[0]
    image = Image.open(BytesIO(requests.get(curinfo[2]).content))
    borders = findborders(image)
    image = image.crop(borders)  # crop image to borders
    maincolor = color_from_image(image)  # get the prevalent color
    background = Image.new("RGB", (480, 480), maincolor)
    background.paste(image, (borders[0], 60 + borders[1]))
    if _index is not None:
        tracklist[_index].append(background.copy())
        tracklist[_index].append(maincolor)
    else:
        return background.copy()


class DlWidget:  # ABSTRACT
    def __init__(s, osi):
        # root superclass constructor has the elements shared by all possible variations of downloader widget
        # create root window with basic border
        s.osi = osi
        s.wrapper = tk.Frame(s.osi.dlframe, height=54)
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
    def __init__(s, osi):
        DlWidget.__init__(s, osi)

    def __str__(s):
        return "GpLine (INTERFACE!)"


# noinspection PyMethodParameters,PyMethodParameters
class GpTrack(GpLine):
    def __init__(s, osi, tracklist):
        GpLine.__init__(s, osi)
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
                                command=lambda: s.osi.dl_delete(s))
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
        s.osi.DLMAN.queue_gp([s.tracklist[s.multi_index]])
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
    def __init__(s, osi, albumlist):
        GpLine.__init__(s, osi)
        s.albumlist = albumlist
        s.multi_index = 0

        s.generate()

    def __str__(s):
        return "GpAlbum"

    def ready(s):  # send relevant data to DownloadManager
        album_tracks = s.osi.api.get_album_info(s.albumlist[s.multi_index][4])["tracks"]
        s.osi.DLMAN.queue_gp([s.osi.gp_get_track_data(x) for x in album_tracks])
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
                                command=lambda: s.osi.dl_delete(s))
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
    def __init__(s, osi, tracklist, plinfo):
        GpLine.__init__(s, osi)
        s.plinfo = plinfo
        s.tracklist = tracklist
        s.generate()

    def __str__(s):
        return "GpPlaylist"

    def ready(s):  # send relevant data to DownloadManager
        s.osi.DLMAN.queue_gp(s.tracklist)
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
                                command=lambda: s.osi.dl_delete(s))
        s.delbutton.pack(side=RIGHT, padx=(0, 8))
        s.readybutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="OK", width=3,
                                  relief='ridge', bd=2, activebackground="green", activeforeground=COLOR_TEXT,
                                  highlightbackground=s.bordercolor, highlightcolor=s.bordercolor, command=s.ready)
        s.readybutton.pack(side=RIGHT, padx=(0, 8))


# noinspection PyMethodParameters
class YtLine(DlWidget):
    def __init__(s, osi):
        DlWidget.__init__(s, osi)

    def __str__(s):
        return "YtLine (INTERFACE!)"


# noinspection PyMethodParameters,PyMethodParameters
class YtSingle(YtLine):
    def __init__(s, osi, tracklist):
        YtLine.__init__(s, osi)
        s.tracklist = tracklist
        s.multi_index = 0  # which song to select in the tracklist
        s.generate()

    def __str__(s):
        return "YtSingle"

    def ready(s):  # send relevant data to DownloadManager
        s.osi.DLMAN.queue_yt([s.tracklist[s.multi_index]])
        s.wrapper.destroy()

    def generate(s):
        DlWidget.generate(s)  # regenerate mainframe

        generate_image_data(s.tracklist, s.multi_index)  # appends image object and primary color to info
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
                                command=lambda: s.osi.dl_delete(s))
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


class YtMulti(YtLine):
    def __init__(s, osi, tracklist, plinfo):
        YtLine.__init__(s, osi)
        s.tracklist = tracklist
        s.plinfo = plinfo
        s.multi_index = 0  # which song to select in the tracklist
        s.generate()

    def __str__(s):
        return "YtMulti"

    def ready(s):
        s.osi.DLMAN.queue_yt(s.tracklist)
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
                                command=lambda: s.osi.dl_delete(s))
        s.delbutton.pack(side=RIGHT, padx=(0, 8))
        s.readybutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="OK", width=3,
                                  relief='ridge', bd=2, activebackground="green", activeforeground=COLOR_TEXT,
                                  highlightbackground=s.bordercolor, highlightcolor=s.bordercolor, command=s.ready)
        s.readybutton.pack(side=RIGHT, padx=(0, 8))